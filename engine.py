import chess
import chess.polyglot
import json
from time import time

filename = "../data/opening_book.json"

tt = {}
tt_quiescence = {}
killer_moves = {}
CENTER_BONUS = []
EXACT = 0
LOWER_BOUND = 1
UPPER_BOUND = 2
for square in range(64):
    rank = square // 8
    file = square % 8
    center_distance = abs(3.5 - rank) + abs(3.5 - file)
    CENTER_BONUS.append((7 - center_distance) * 0.1)

piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

PAWN_TABLE = [
      0,   0,   0,   0,   0,   0,   0,   0,
      5,  10,  10,  10,  10,  10,  10,   5,
    -10, -10,   0,  30,  30,   0, -10, -10,
    -10, -10,   0,  50,  50,   0, -10, -10,
     30,  30,  40,  60,  60,  40,  30,  30,
     60,  60,  70,  90,  90,  70,  60,  60,
    200, 200, 200, 200, 200, 200, 200, 200,
      0,   0,   0,   0,   0,   0,   0,   0
]

def count_diagonal_squares(square):
    rank = square // 8
    file = square % 8
    return min(rank, file) + min(7-rank, 7-file) + min(rank, 7-file) + min(7-rank, file)

BISHOP_MOBILITY = [count_diagonal_squares(sq) for sq in range(64)]
def gives_checkmate(board, move):
    board.push(move)
    try:
        return board.is_checkmate()
    finally:
        board.pop()

def is_endgame_from_board(board):
    total_material = sum(
        piece_values[board.piece_type_at(sq)]
        for sq in chess.SQUARES
        if board.piece_at(sq) and board.piece_type_at(sq) != chess.KING
    )
    
    return total_material <= 2500

def find_opening(board, openings_data):
    current_fen = board.fen()
    if current_fen not in openings_data:
        return None
    
    position_data = openings_data[current_fen]
    possible_moves = position_data.get("moves", [])
    legal_moves = list(board.legal_moves)

    for data_move in possible_moves:
        if data_move in legal_moves:
            return move
    
    return None

def order_moves(board, moves, depth, tt_move=None):
    captures = []
    quiet_moves = []

    scored_moves = []
    for move in moves:
        score = 0
        if tt_move and move == tt_move:
            score = 1000000
        elif board.is_capture(move):
            victim = board.piece_type_at(move.to_square)
            attacker = board.piece_type_at(move.from_square)
            score = piece_values.get(victim, 0) * 10 - piece_values.get(attacker, 0) + 10000
        elif depth in killer_moves and move in killer_moves[depth]:
            score = 9000
            
        scored_moves.append((score, move))
    
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    return [m[1] for m in scored_moves]

def evaluate(board):
    if board.is_checkmate():
        return -1000000
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    total_material = sum(
        piece_values[board.piece_type_at(sq)]
        for sq in chess.SQUARES
        if board.piece_at(sq) and board.piece_type_at(sq) != chess.KING
    )

    if board.fullmove_number < 12:
        if board.piece_at(chess.B1) == chess.Piece(chess.KNIGHT, chess.WHITE):
            score -= 10
        if board.piece_at(chess.G1) == chess.Piece(chess.KNIGHT, chess.WHITE):
            score -= 10
        if board.piece_at(chess.C1) == chess.Piece(chess.BISHOP, chess.WHITE):
            score -= 8
        if board.piece_at(chess.F1) == chess.Piece(chess.BISHOP, chess.WHITE):
            score -= 8
        if board.piece_at(chess.D2) == chess.Piece(chess.PAWN, chess.WHITE):
            score -= 15
        if board.piece_at(chess.E2) == chess.Piece(chess.PAWN, chess.WHITE):
            score -= 15
        if board.has_castling_rights(chess.WHITE):
            if board.piece_at(chess.F2) is None:
                score -= 40
        
        if board.piece_at(chess.B8) == chess.Piece(chess.KNIGHT, chess.BLACK):
            score += 10
        if board.piece_at(chess.G8) == chess.Piece(chess.KNIGHT, chess.BLACK):
            score += 10
        if board.piece_at(chess.C8) == chess.Piece(chess.BISHOP, chess.BLACK):
            score += 8
        if board.piece_at(chess.F8) == chess.Piece(chess.BISHOP, chess.BLACK):
            score += 8
        if board.piece_at(chess.D7) == chess.Piece(chess.PAWN, chess.BLACK):
            score += 15
        if board.piece_at(chess.E7) == chess.Piece(chess.PAWN, chess.BLACK):
            score += 15
        if not board.has_castling_rights(chess.BLACK):
            if board.piece_at(chess.F7) is None:
                score += 40
    
    is_endgame = total_material <= 2500
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue

        value = piece_values[piece.piece_type]
        piece_type = piece.piece_type
        piece_clr = piece.color
        if piece_type == chess.KNIGHT:
            value += CENTER_BONUS[square]
        elif piece_type == chess.PAWN:
            if piece_clr == chess.WHITE:
                value += PAWN_TABLE[square] * 0.5
            else:
                value += PAWN_TABLE[63 - square] * 0.5
            if is_endgame:
                value += 50
                rank = square // 8
                file = square % 8

                if piece.color == chess.WHITE:
                    value += rank * 10
                    is_passed = True
                    for r in range(rank + 1, 8):
                        for f in [file - 1, file, file + 1]:
                            if 0 <= f < 8:
                                sq = r * 8 + f
                                p = board.piece_at(sq)
                                if p and p.piece_type == chess.PAWN and p.color == chess.BLACK:
                                    is_passed = False
                                    break
                        if not is_passed:
                            break
                    
                    if is_passed:
                        value += rank * 15
                else:
                    value += (7 - rank) * 10
                    is_passed = True
                    for r in range(rank - 1, -1, -1):
                        for f in [file - 1, file, file + 1]:
                            if 0 <= f < 8:
                                sq = r * 8 + f
                                p = board.piece_at(sq)
                                if p and p.piece_type == chess.PAWN and p.color == chess.WHITE:
                                    is_passed = False
                                    break
                        if not is_passed:
                            break
                    
                    if is_passed:
                        value += (7 - rank) * 15
        elif piece_type == chess.BISHOP:
            value += BISHOP_MOBILITY[square] * 2
        elif piece_type == chess.KING:
            if board.fullmove_number < 20:
                value -= CENTER_BONUS[square] * 50
            
            if piece.color == chess.WHITE:
                if not board.has_kingside_castling_rights(chess.WHITE) and not board.has_queenside_castling_rights(chess.WHITE):
                    if square in [chess.G1, chess.C1]:
                        value += 30
            else:
                if not board.has_kingside_castling_rights(chess.BLACK) and not board.has_queenside_castling_rights(chess.BLACK):
                    if square in [chess.G8, chess.C8]:
                        value += 30
        
        score += value if piece.color == chess.WHITE else -value
    
    legal_moves = list(board.legal_moves)
    if not board.is_check() and len(legal_moves) > 0:
        score += len(legal_moves) * 0.5

    if board.turn == chess.WHITE:
        return score
    else:
        return -score

def see_capture(board, move):
    if not board.is_capture(move):
        return 0
    
    victim = board.piece_type_at(move.to_square)
    if victim is None:
        victim_value = piece_values[chess.PAWN]
    else:
        victim_value = piece_values[victim]
    
    attacker_value = piece_values[board.piece_type_at(move.from_square)]
    
    board.push(move)
    is_attacked = not board.is_attacked_by(board.turn, move.to_square)
    board.pop()
    
    if is_attacked:
        return victim_value

    gain = victim_value - attacker_value
    return gain

def quiescence(board, alpha=float("-inf"), beta=float("inf"), depth=0):
    zobrist = chess.polyglot.zobrist_hash(board)
    alpha_orig = alpha

    if zobrist in tt_quiescence:
        cached_score, cached_bound = tt_quiescence[zobrist]
        if cached_bound == EXACT:
            return cached_score
        elif cached_bound == LOWER_BOUND:
            alpha = max(alpha, cached_score)
        elif cached_bound == UPPER_BOUND:
            beta = min(beta, cached_score)
        
        if alpha >= beta:
            return cached_score

    if depth >= 7:
        return evaluate(board)
    
    stand_pat = evaluate(board)
    if stand_pat >= beta:
        return beta
    
    BIG_DELTA = 900
    if stand_pat < alpha - BIG_DELTA:
        return alpha
    if stand_pat > alpha:
        alpha = stand_pat
    
    forcing_moves = [move for move in board.legal_moves if board.is_capture(move) or board.gives_check(move)]
    forcing_moves.sort(key=lambda m:
        piece_values.get(board.piece_type_at(m.to_square), 1) * 10 
        -piece_values[board.piece_type_at(m.from_square)],
        reverse=True)

    for move in forcing_moves:
        see_score = see_capture(board, move)
        if see_score < -1:
            continue

        victim_value = piece_values.get(board.piece_type_at(move.to_square), 1)
        if stand_pat + victim_value + 300 < alpha:
            continue

        board.push(move)
        score = -quiescence(board, -beta, -alpha, depth + 1)
        board.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    
    if alpha >= beta:
        tt_quiescence[zobrist] = (beta, LOWER_BOUND)
    elif alpha > alpha_orig:
        tt_quiescence[zobrist] = (alpha, EXACT)
    else:
        tt_quiescence[zobrist] = (alpha, UPPER_BOUND)
    
    return alpha

def minimax(board, depth, alpha=float("-inf"), beta=float("inf"), ply=0, null_move_allowed=True):
    legal_moves = board.legal_moves
    if board.is_checkmate() and len(list(legal_moves)) <= 0:
        return -1000000 + depth
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    if board.can_claim_threefold_repetition():
        return -50
    if board.is_repetition(2):
        return -20
    if depth == 0:
        if board.is_check():
            depth += 1
        else:
            return quiescence(board)

    board_hash = chess.polyglot.zobrist_hash(board)
    alpha_orig = alpha
    tt_move = None
    
    if board_hash in tt:
        cached_depth, cached_score, cached_bound, cached_move = tt[board_hash]
        if cached_depth >= depth:
            if cached_bound == EXACT:
                return cached_score
            elif cached_bound == LOWER_BOUND:
                alpha = max(alpha, cached_score)
            elif cached_bound == UPPER_BOUND:
                beta = min(beta, cached_score)
            
            if alpha >= beta:
                return cached_score
        
        tt_move = cached_move

    NULL_MOVE_REDUCTION = 2
    if (depth >= 3 and not board.is_check() and ply > 0 and not is_endgame_from_board(board) and null_move_allowed):
        board.push(chess.Move.null())
        null_score = -minimax(board, depth - 1 - NULL_MOVE_REDUCTION, -beta, -beta + 1, ply + 1, False)
        board.pop()

        if null_score >= beta:
            return beta
    
    max_score = float("-inf")
    best_move = None
    moves = order_moves(board, legal_moves, depth, tt_move)    
    for idx, move in enumerate(moves):
        if gives_checkmate(board, move):
            mate_score = 1000000 - ply * 1000
            tt[board_hash] = (depth, mate_score, EXACT, move)
            return mate_score
        
        is_check = board.gives_check(move)
        
        board.push(move)
        if idx < 4 or board.is_capture(move) or is_check:
            score = -minimax(board, depth - 1, -beta, -alpha, ply + 1)
        else:
            reduction = 1 if depth > 3 else 0
            score = -minimax(board, depth - 1 - reduction, -beta, -alpha, ply + 1)

            if score > alpha:
                score = -minimax(board, depth - 1, -beta, -alpha, ply + 1)
        board.pop()

        if score > max_score:
            max_score = score
            best_move = move

        alpha = max(alpha, score)
        if alpha >= beta:
            if not board.is_capture(move):
                if depth not in killer_moves:
                    killer_moves[depth] = []
                if move not in killer_moves[depth]:
                    killer_moves[depth].insert(0, move)
                    if len(killer_moves[depth]) > 2:
                        killer_moves[depth].pop()
            break
    
    if max_score >= beta:
        tt[board_hash] = (depth, max_score, LOWER_BOUND, best_move)
    elif max_score > alpha_orig:
        tt[board_hash] = (depth, max_score, EXACT, best_move)
    else:
        tt[board_hash] = (depth, max_score, UPPER_BOUND, best_move)
    
    return max_score

def get_best_move(board, max_depth):
    tt.clear()
    tt_quiescence.clear()

    legal_moves = list(board.legal_moves)
    try:
        with open(filename, "r") as f:
            openings = json.load(f)
        
        if board.ply() < 15:
            move = find_opening(board, openings)
            if move:
                return move
    except FileNotFoundError:
        print("File not found.")

    best_move = None
    best_score = float("-inf")
    alpha = float("-inf")
    beta = float("inf")

    board_hash = chess.polyglot.zobrist_hash(board)
    tt_move = tt[board_hash][3] if board_hash in tt else None
    moves = order_moves(board, legal_moves, max_depth, tt_move)
    evaluations = []
    
    for move in moves:
        if gives_checkmate(board, move):
            return move
        
        board.push(move)
        score = -minimax(board, max_depth - 1, -beta, -alpha, 1)
        board.pop()

        evaluations.append((move, score))
        if score > best_score:
            best_score = score
            best_move = move
            alpha = max(alpha, score)

    return best_move

def get_move_format(board, move_str):
    try:
        move = chess.Move.from_uci(move_str)
        if move in board.legal_moves:
            return "uci"
    except Exception:
        pass

    try:
        move = board.parse_san(move_str)
        if move in board.legal_moves:
            return "san"
    except Exception:
        pass

    return None

board = chess.Board()
if __name__ == "__main__":
    for _ in range(5):
        move = input("Move: ")
        if move:
            format = get_move_format(board, move)
            if format == "uci":
                board.push_uci(move)
            elif format == "san":
                board.push_san(move)
            else:
                print("Illegal move / Invalid notation")
                break

        start = time()
        best_move = get_best_move(board, 4)
        end = time()
        time_taken = round(end - start, 2)
    
        print(board.san(best_move) + f" ({time_taken}s)")
        board.push(best_move)
        print()
