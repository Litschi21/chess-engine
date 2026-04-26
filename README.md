# chess-engine
A simple human-like chess engine written in Python.

## Features
Search Algorithms: Minimax with Alpha-Beta pruning.
Optimization:
* Transposition Table (TT): Uses Zobrist hashing to cache previously evaluated positions.
* Quiescence Search: Prevents the "horizon effect" by extending searches until positions are tactically stable.
* Move Ordering: Prioritizes captures, killer moves, and TT-suggested moves to maximize pruning efficiency.

## Elo at different depths
* Depth 1: ~1000 ELO
* Depth 2: ~1300 ELO
* Depth 3: ~1500 ELO
* Depth 4: ~1900 ELO
* Depth 5: ~2000 ELO
* Depth 6: ~2200 ELO

## Prerequisites
```bash
pip install -r requirements.txt
```

## Usage
Ensure your opening_book.json is located in the same directory as the python file.

Run the engine:
```bash
python engine.py
```
Enter moves using either UCI (e.g., e2e4) or SAN (e.g., e4) notation.

## License
This project is open-source and available for personal use.
