import tkinter as tk
from tkinter import Tk, Canvas, Label, Button, Frame, PhotoImage, Toplevel, messagebox
import time
from PIL import Image, ImageTk
import os
import random

class Board:
    def __init__(self):
        self.grid = [[None] * 8 for i in range(8)]
        self.turn = "light"
        self.selected = None
        self.legal_moves = []
        self.castling = {
            "light": {"kingside": True, "queenside": True},
            "dark": {"kingside": True, "queenside": True}
        }
        self.move_history = []
        self.en_passant_target = None
        self.status = "playing"
        self.promotion_pending = None
        self.game_started = False

    def setup_pieces(self):
        pieces = ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]

        for row in range(len(self.grid)):
            for col in range(len(self.grid[0])):

                #* Row Back Rank
                if row in (0, 7):
                    piece = pieces[col]
                    if row == 0:
                        self.grid[row][col] = Piece("dark", piece, row, col)
                    else:
                        self.grid[row][col] = Piece("light", piece, row, col)

                #* Pawn Rank
                elif row in (1, 6):
                    piece = "pawn"
                    if row == 1:
                        self.grid[row][col] = Piece("dark", piece, row, col)
                    else:
                        self.grid[row][col] = Piece("light", piece, row, col)

                #* Empty Rank
                else:
                    continue

    def move_piece(self, from_where, to):
        #* 1.
        piece = self.grid[from_where[0]][from_where[1]]
        self.grid[to[0]][to[1]] = piece
        self.grid[from_where[0]][from_where[1]] = None

        #* 2.
        piece.row = to[0]
        piece.col = to[1]

        #* 3.
        piece.has_moved = True

        #* 4.
        if piece.piece_type == "pawn" and to == self.en_passant_target:
            self.grid[from_where[0]][to[1]] = None

        #* 5.
        if piece.piece_type == "pawn" and abs(to[0] - from_where[0]) == 2:
            self.en_passant_target = ((from_where[0] + to[0]) // 2, to[1])
        else:
            self.en_passant_target = None

        #* 6.
        if piece.piece_type == "king" and abs(to[1] - from_where[1]) == 2:
            if to[1] > from_where[1]:
                rook = self.grid[from_where[0]][7]
                self.grid[from_where[0]][5] = rook
                self.grid[from_where[0]][7] = None
                rook.col = 5
                rook.has_moved = True

            if to[1] < from_where[1]:
                rook = self.grid[from_where[0]][0]
                self.grid[from_where[0]][3] = rook
                self.grid[from_where[0]][0] = None
                rook.col = 3
                rook.has_moved = True

        #* 7.
        if piece.piece_type == "king":
            self.castling[piece.color]["kingside"] = False
            self.castling[piece.color]["queenside"] = False

        if piece.piece_type == "rook":
            if from_where[1] == 7:
                self.castling[piece.color]["kingside"] = False
            if from_where[1] == 0:
                self.castling[piece.color]["queenside"] = False

        #* 8.
        self.move_history.append((from_where, to))
        self.game_started = True

        #* 9.
        if piece.piece_type == "pawn":
            if (piece.color == "light" and to[0] == 0) or (piece.color == "dark" and to[0] == 7):
                self.promotion_pending = (to[0], to[1])

        #* 10.
        if self.promotion_pending is None:
            if self.turn == "light":
                self.turn = "dark"
            elif self.turn == "dark":
                self.turn = "light"

        #* 11.
        if self.is_in_checkmate(self.turn):
            self.status = f"checkmate_{self.turn}"
        elif self.is_in_stalemate(self.turn):
            self.status = "stalemate"

    def get_legal_move(self, row, col):
        legal = []
        piece = self.grid[row][col]
        if piece is None:
            return legal
        
        all_moves = piece.get_moves(self)
        if piece.piece_type == "king" and self.is_in_check(piece.color):
            all_moves = [(r, c) for r, c in all_moves if abs(c - col) != 2]

        for target_row, target_col in all_moves:
            targeted = self.grid[target_row][target_col]
            ep_backup = self.en_passant_target

            orig_row, orig_col = piece.row, piece.col

            self.grid[target_row][target_col] = piece
            self.grid[row][col] = None
            piece.row = target_row
            piece.col = target_col

            if not self.is_in_check(piece.color):
                if piece.piece_type == "king" and abs(target_col - orig_col) == 2:
                    passed_col = (orig_col + target_col) // 2
                    if not self.is_square_attacked(orig_row, passed_col, piece.color) and not self.is_in_check(piece.color):
                        legal.append((target_row, target_col))
                else:
                    legal.append((target_row, target_col))

            self.grid[row][col] = piece
            self.grid[target_row][target_col] = targeted
            piece.row = orig_row
            piece.col = orig_col
            self.en_passant_target = ep_backup

        return legal

    def is_square_attacked(self, row, col, our_color):
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p is not None and p.color != our_color:
                    if (row, col) in p.get_moves(self):
                        return True
        return False
    
    def is_in_check(self, color):
        king_pos = None

        #* Loop the king's position
        for r in range(len(self.grid)):
            for c in range(len(self.grid[0])):
                if self.grid[r][c] is not None and self.grid[r][c].piece_type == "king" and self.grid[r][c].color == color:
                    king_pos = (r, c)

        #* Loop the enemy's position
        for r in range(len(self.grid)):
            for c in range(len(self.grid[0])):
                piece = self.grid[r][c]
                if piece is not None and piece.color != color:
                    enemy_move = piece.get_moves(self)
                    if king_pos in enemy_move:
                        return True
        
        return False

    def is_in_checkmate(self, color):
        if not self.is_in_check(color):
            return False
        
        for r in range(len(self.grid)):
            for c in range(len(self.grid[0])):
                piece = self.grid[r][c]
                if piece is not None and piece.color == color:
                    legal = self.get_legal_move(r, c)
                    if legal:
                        return False
                
        return True

    def is_in_stalemate(self, color):
        if self.is_in_check(color):
            return False
        
        for r in range(len(self.grid)):
            for c in range(len(self.grid[0])):
                piece = self.grid[r][c]
                if piece is not None and piece.color == color:
                    legal = self.get_legal_move(r, c)
                    if legal:
                        return False
                
        return True
    
    def get_legal_moves_ai(self, color):
        moves = []

        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]

                if piece is not None and piece.color == color:
                    moves_legally = self.get_legal_move(row, col)

                    for r, c in moves_legally:
                        moves.append( ((row, col), (r, c)) )
        
        return moves

class Piece:
    def __init__(self, color, piece_type, row, col):
        self.color = color
        self.piece_type = piece_type
        self.row = row
        self.col = col
        self.has_moved = False
        self.image = None

    def get_moves(self, board):
        #* 1st function
        def is_out_board(r, c):
            if 0 <= r <= 7 and 0 <= c <= 7:
                return False
            return True
        
        #* 2nd function
        def is_empty(r, c):
            return board.grid[r][c] is None if not is_out_board(r, c) else False

        #* 3rd function
        def is_enemy(r, c, color):
            return board.grid[r][c] is not None and board.grid[r][c].color != color

        moves = []

        if self.piece_type == "rook":
            for i in range(4):
                chain = 1
                if i == 0:
                    x = 0
                    y = 1
                elif i == 1:
                    x = 0
                    y = -1
                elif i == 2:
                    x = 1
                    y = 0
                else:
                    x = -1
                    y = 0

                while True:
                    target = (self.row + (chain * x), self.col + (chain * y))
                    if is_out_board(target[0], target[1]):
                        break
                    elif is_empty(target[0], target[1]):
                        moves.append(target)
                    elif is_enemy(target[0], target[1], self.color):
                        moves.append(target)
                        break
                    else:
                        break
                    chain += 1

        elif self.piece_type == "knight":
            targets = [(1, 2), (1, -2), (2, 1), (2, -1), (-1, 2), (-1, -2), (-2, 1), (-2, -1)]
            for i in range(8):
                target = (self.row + targets[i][0], self.col + targets[i][1])
                if is_out_board(target[0], target[1]):
                    continue
                elif is_empty(target[0], target[1]):
                    moves.append(target)
                elif is_enemy(target[0], target[1], self.color):
                    moves.append(target)
                else:
                    continue

        elif self.piece_type == "bishop":
            for i in range(4):
                chain = 1
                if i == 0:
                    x = 1
                    y = 1
                elif i == 1:
                    x = -1
                    y = -1
                elif i == 2:
                    x = 1
                    y = -1
                else:
                    x = -1
                    y = 1

                while True:
                    target = (self.row + (chain * x), self.col + (chain * y))
                    if is_out_board(target[0], target[1]):
                        break
                    elif is_empty(target[0], target[1]):
                        moves.append(target)
                    elif is_enemy(target[0], target[1], self.color):
                        moves.append(target)
                        break
                    else:
                        break
                    chain += 1

        elif self.piece_type == "queen":
            targets = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
            for i in range(8):
                chain = 1
                x, y = targets[i]
                while True:
                    target = (self.row + (chain * x), self.col + (chain * y))
                    if is_out_board(target[0], target[1]):
                        break
                    elif is_empty(target[0], target[1]):
                        moves.append(target)
                    elif is_enemy(target[0], target[1], self.color):
                        moves.append(target)
                        break
                    else:
                        break
                    chain += 1

        elif self.piece_type == "king":
            targets = [(1, 0), (1, 1), (1, -1), (-1, 0), (-1, 1), (-1, -1), (0, 1), (0, -1)]
            for i in range(8):
                target = (self.row + targets[i][0], self.col + targets[i][1])
                if is_out_board(target[0], target[1]):
                    continue
                elif is_empty(target[0], target[1]):
                    moves.append(target)
                elif is_enemy(target[0], target[1], self.color):
                    moves.append(target)
                else:
                    continue

            if self.has_moved == False:
                if board.castling[self.color]["kingside"]:
                    if board.grid[self.row][5] is None and board.grid[self.row][6] is None:
                        moves.append((self.row, 6))

                if board.castling[self.color]["queenside"]:
                    if board.grid[self.row][1] is None and board.grid[self.row][2] is None and board.grid[self.row][3] is None:
                        moves.append((self.row, 2))

        elif self.piece_type == "pawn":
            direction = -1 if self.color == "light" else 1
            if is_empty(self.row + direction, self.col):
                moves.append((self.row + direction, self.col))
                
                if not self.has_moved:
                    if is_empty(self.row + direction*2, self.col):
                        moves.append((self.row + direction*2, self.col))
            
            if not is_out_board(self.row + direction, self.col - 1) and is_enemy(self.row + direction, self.col - 1, self.color):
                moves.append((self.row + direction, self.col - 1))
            if not is_out_board(self.row + direction, self.col + 1) and is_enemy(self.row + direction, self.col + 1, self.color):
                moves.append((self.row + direction, self.col + 1))

            left_ep = (self.row + direction, self.col - 1)
            right_ep = (self.row + direction, self.col + 1)
            if left_ep == board.en_passant_target:
                moves.append((left_ep))
            if right_ep == board.en_passant_target:
                moves.append((right_ep))
            
        return moves

    def load_image(self, size):
        filename = f"{self.color}_{self.piece_type}.png" 
        ori_path = r"C:\Users\User\Documents\Python\chess" 
        path = os.path.join(ori_path, filename) 
        image = Image.open(path) 
        image = image.convert("RGBA")
        image = image.resize((size, size)) 
        image = ImageTk.PhotoImage(image) 
        self.image = image

class AI:
    def __init__(self):
        self.color = "dark"
        self.enemy_color = "light"
        self.piece_value = {
            "pawn": 100,
            "knight": 320,
            "bishop": 330,
            "rook": 500,
            "queen": 900,
            "king": 20000
        }
        self.pawn_table = [
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [ 5,  5, 10, 25, 25, 10,  5,  5],
            [ 0,  0,  0, 20, 20,  0,  0,  0],
            [ 5, -5,-10,  0,  0,-10, -5,  5],
            [ 5, 10, 10,-20,-20, 10, 10,  5],
            [ 0,  0,  0,  0,  0,  0,  0,  0]
        ]

        self.knight_table = [
            [-50,-40,-30,-30,-30,-30,-40,-50],
            [-40,-20,  0,  0,  0,  0,-20,-40],
            [-30,  0, 10, 15, 15, 10,  0,-30],
            [-30,  5, 15, 20, 20, 15,  5,-30],
            [-30,  0, 15, 20, 20, 15,  0,-30],
            [-30,  5, 10, 15, 15, 10,  5,-30],
            [-40,-20,  0,  5,  5,  0,-20,-40],
            [-50,-40,-30,-30,-30,-30,-40,-50]
        ]

        self.bishop_table = [
            [-20,-10,-10,-10,-10,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5, 10, 10,  5,  0,-10],
            [-10,  5,  5, 10, 10,  5,  5,-10],
            [-10,  0, 10, 10, 10, 10,  0,-10],
            [-10, 10, 10, 10, 10, 10, 10,-10],
            [-10,  5,  0,  0,  0,  0,  5,-10],
            [-20,-10,-10,-10,-10,-10,-10,-20]
        ]

        self.rook_table = [
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 5, 10, 10, 10, 10, 10, 10,  5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [ 0,  0,  0,  5,  5,  0,  0,  0]
        ]

        self.queen_table = [
            [-20,-10,-10, -5, -5,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5,  5,  5,  5,  0,-10],
            [ -5,  0,  5,  5,  5,  5,  0, -5],
            [  0,  0,  5,  5,  5,  5,  0, -5],
            [-10,  5,  5,  5,  5,  5,  0,-10],
            [-10,  0,  5,  0,  0,  0,  0,-10],
            [-20,-10,-10, -5, -5,-10,-10,-20]
        ]

        self.king_table = [
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-20,-30,-30,-40,-40,-30,-30,-20],
            [-10,-20,-20,-20,-20,-20,-20,-10],
            [ 20, 20,  0,  0,  0,  0, 20, 20],
            [ 20, 30, 10,  0,  0, 10, 30, 20]
        ]

        self.tables = {
            "pawn": self.pawn_table,
            "knight": self.knight_table,
            "bishop": self.bishop_table,
            "rook": self.rook_table,
            "queen": self.queen_table,
            "king": self.king_table
        }

    def is_checkmate_move(self, board, from_pos, to_pos):
        moved_piece = board.grid[from_pos[0]][from_pos[1]]
        target_backup = board.grid[to_pos[0]][to_pos[1]]
        orig_row, orig_col = moved_piece.row, moved_piece.col

        moved_piece.row, moved_piece.col = to_pos[0], to_pos[1]
        board.grid[to_pos[0]][to_pos[1]] = moved_piece
        board.grid[from_pos[0]][from_pos[1]] = None

        result = board.is_in_checkmate(self.enemy_color)

        board.grid[from_pos[0]][from_pos[1]] = moved_piece
        board.grid[to_pos[0]][to_pos[1]] = target_backup
        moved_piece.row, moved_piece.col = orig_row, orig_col

        return result

    def easy_bot(self, board):
        all_moves = board.get_legal_moves_ai(self.color)
        if not all_moves:
            return None
            
        capturing_moves = []
        for (from_pos, to_pos) in all_moves:
            if self.is_checkmate_move(board, from_pos, to_pos):
                return (from_pos, to_pos)
            
            target_piece = board.grid[to_pos[0]][to_pos[1]]
            if target_piece is not None:
                capturing_moves.append((from_pos, to_pos))

        if capturing_moves:
            return random.choice(capturing_moves)
        
        best_move = random.choice(all_moves)
        return best_move

    def evaluate_board(self, board, is_hard):
        if board.is_in_checkmate(self.enemy_color): return float("inf")
        if board.is_in_checkmate(self.color): return float("-inf")
        if board.is_in_stalemate(self.enemy_color): return 0

        total_score = 0
        for row in range(8):
            for col in range(8):
                square = board.grid[row][col]
                if square is not None:
                    val = self.piece_value[square.piece_type]

                    pos_score = 0
                    if is_hard:
                        row_index = 7 - row if square.color == 'light' else row
                        pos_score = self.tables[square.piece_type][row_index][col]

                    if square.color == self.color:
                        total_score += (val + pos_score)
                    else:
                        total_score -= (val + pos_score)
                        
        return total_score

    def minimax(self, board, depth, alpha, beta, is_maximazing, is_hard, use_ab):
        if depth == 0 or board.status == "game_over":
            return self.evaluate_board(board, is_hard), None
            
        best_move = None
        
        if is_maximazing:
            high_score = float("-inf")
            all_moves = board.get_legal_moves_ai(self.color)
            if not all_moves:
                if board.is_in_check(self.color):
                    return -99999 + (4 - depth), None
                return 0, None
            
            for (from_pos, to_pos) in all_moves:
                moved_piece = board.grid[from_pos[0]][from_pos[1]]
                target_backup = board.grid[to_pos[0]][to_pos[1]]
                orig_row, orig_col = moved_piece.row, moved_piece.col
                
                moved_piece.row, moved_piece.col = to_pos[0], to_pos[1]
                board.grid[to_pos[0]][to_pos[1]] = moved_piece
                board.grid[from_pos[0]][from_pos[1]] = None

                score, _ = self.minimax(board, depth - 1, alpha, beta, False, is_hard, use_ab)
                
                board.grid[from_pos[0]][from_pos[1]] = moved_piece
                board.grid[to_pos[0]][to_pos[1]] = target_backup
                moved_piece.row, moved_piece.col = orig_row, orig_col

                if score > high_score:
                    high_score = score
                    best_move = (from_pos, to_pos)
                
                if use_ab:
                    alpha = max(alpha, score)
                    if beta <= alpha: break
            return high_score, best_move

        else:
            low_score = float("inf")
            all_moves = board.get_legal_moves_ai(self.enemy_color)
            if not all_moves:
                if board.is_in_check(self.enemy_color):
                    return 99999 - (4 - depth), None
                return 0, None
            
            for (from_pos, to_pos) in all_moves:
                moved_piece = board.grid[from_pos[0]][from_pos[1]]
                target_backup = board.grid[to_pos[0]][to_pos[1]]
                orig_row, orig_col = moved_piece.row, moved_piece.col
                
                moved_piece.row, moved_piece.col = to_pos[0], to_pos[1]
                board.grid[to_pos[0]][to_pos[1]] = moved_piece
                board.grid[from_pos[0]][from_pos[1]] = None
                
                score, _ = self.minimax(board, depth - 1, alpha, beta, True, is_hard, use_ab)
                
                board.grid[from_pos[0]][from_pos[1]] = moved_piece
                board.grid[to_pos[0]][to_pos[1]] = target_backup
                moved_piece.row, moved_piece.col = orig_row, orig_col

                if score < low_score:
                    low_score = score
                    best_move = (from_pos, to_pos)
                
                if use_ab:
                    beta = min(beta, score)
                    if beta <= alpha: break
            return low_score, best_move
        
    def medium_bot(self, board):
        _, best_move = self.minimax(board, depth=3, alpha=None, beta=None, is_maximazing=True, is_hard=False, use_ab=False)
        return best_move if best_move else self.easy_bot(board)

    def hard_bot(self, board):
        _, final_step = self.minimax(board, depth=4, alpha=float("-inf"), beta=float("inf"), is_maximazing=True, is_hard=True, use_ab=True)
        return final_step if final_step else self.easy_bot(board)

class Timer:
    def __init__(self):
        self.light_time = 600
        self.dark_time = 600
        self.active = "light"
        self.running = False

    def start(self, color):
        self.active = color
        self.running = True

    def stop(self):
        self.running = False

    def tick(self):
        if self.running == False:
            return 
        
        if self.active == "light":
            self.light_time -= 1
        if self.active == "dark":
            self.dark_time -= 1

        if self.is_timeout(self.active):
            self.stop()
            return

    def get_display(self, color):
        timing = self.light_time if color == "light" else self.dark_time
        minutes = timing // 60
        seconds = timing % 60
        return f"{minutes:02}:{seconds:02}"

    def is_timeout(self, color):
        if color == "light":
            return self.light_time <= 0
        elif color == "dark":
            return self.dark_time <= 0

class ChessApp(Tk):
    def __init__(self):
        super().__init__()
        self.geometry("900x900")
        self.title("Chess")

        self.board = Board()
        self.board.setup_pieces()

        self.bot = AI()
        self.timing = Timer()

        self.board_size = 640
        self.title_size = self.board_size // 8

        self.canvas = Canvas(
            self,
            width = self.board_size,
            height= self.board_size
        )
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.pack(pady=20, padx=20)

        self.control_frame = Frame(self)
        self.control_frame.pack(side="bottom", pady=20)
        
        self.dark_timer_label = Label(self.control_frame, text="Dark: 10:00", font=("Arial", 14))
        self.dark_timer_label.pack(side="left", padx=20)

        ai_frame = Frame(self.control_frame)
        ai_frame.pack(side="left", padx=5)
        Label(ai_frame, text="Level AI:").pack()
        self.ai_level = tk.StringVar(value="Hard")
        self.ai_menu = tk.OptionMenu(ai_frame, self.ai_level, "Human", "Easy", "Medium", "Hard")
        self.ai_menu.pack()

        self.history_box = tk.Text(self.control_frame, width=30, height=20, state="disabled")
        self.history_box.pack(side="left", padx=10)

        self.resign_btn = Button(self.control_frame, text="Resign", command=self.resign_game)
        self.resign_btn.pack(side="left", padx=20)

        self.light_timer_label = Label(self.control_frame, text="Light: 10:00", font=("Arial", 14))
        self.light_timer_label.pack(side="right", padx=20)

        self.load_board_images()
        self.draw_board()
        self.draw_pieces()

    def load_board_images(self):
        for row in range(8):
            for col in range(8):
                piece = self.board.grid[row][col]

                if piece is not None:
                    piece.load_image(self.title_size)
    
    def draw_board(self):
        colors = ("#F0D9B5", "#B58863")

        for row in range(8):
            for col in range(8):

                color = colors[(row + col) % 2]

                x1 = col * self.title_size
                y1 = row * self.title_size

                x2 = x1 + self.title_size
                y2 = y1 + self.title_size

                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=color,
                    outline=""
                )

    def draw_pieces(self):
        for row in range(8):
            for col in range(8):
                piece = self.board.grid[row][col]

                if piece is None:
                    continue

                x = col * self.title_size + self.title_size // 2
                y = row * self.title_size + self.title_size // 2

                self.canvas.create_image(
                    x,
                    y,
                    image = piece.image
                )

    def on_click(self, event):
        if self.board.status != "playing":
            return
        if self.ai_level.get() != "Human" and self.board.turn == "dark":
            return
    
        col = event.x // self.title_size
        row = event.y // self.title_size
        piece = self.board.grid[row][col]

        if row > 7 and col > 7:
            return 

        if self.board.selected is None:
            if piece is not None and piece.color == self.board.turn:
                self.board.selected = (row, col)
                self.board.legal_moves = self.board.get_legal_move(row, col)
                self.render()

        else:
            if (row, col) in self.board.legal_moves:
                self.board.move_piece(self.board.selected, (row, col))
                self.timing.start(self.board.turn)
                if len(self.board.move_history) == 1:
                    self.after(1000, self.tick_time)
                self.board.selected = None
                self.board.legal_moves = []
                self.render()
            elif piece is not None and piece.color == self.board.turn:
                self.board.selected = (row, col)
                self.board.legal_moves = self.board.get_legal_move(row, col)
                self.render()
            else:
                self.board.selected = None
                self.board.legal_moves = []
                self.render()

        if self.board.turn == "dark" and self.board.status == "playing":
            self.after(500, self.execute_ai_move)

    def execute_ai_move(self):
        move = self.get_ai_move()
        if move:
            self.board.move_piece(move[0], move[1])
            self.timing.start(self.board.turn)
            self.render()

            if self.board.status != "playing":
                self.render()

    def get_ai_move(self):
        level = self.ai_level.get()
        
        if level == "Human":
            return None
        elif level == "Easy":
            return self.bot.easy_bot(self.board)
        elif level == "Medium":
            return self.bot.medium_bot(self.board)
        elif level == "Hard":
            return self.bot.hard_bot(self.board)
        return None
    
    def resign_game(self):
        if self.board.status == "playing":
            if self.ai_level.get() == "Human":
                winner = "Dark" if self.board.turn == "light" else "Light"
                loser = "Light" if self.board.turn == "light" else "Dark"
                messagebox.showinfo("Game Over", f"{loser} give up! {winner} wins!")
            else:
                messagebox.showinfo("Game Over", "You give up! AI wins!")
            self.board.status = "game_over"
            self.render()

    def show_promotion(self):
        row, col = self.board.promotion_pending
        piece = self.board.grid[row][col]
        self.board.promotion_pending = None

        #* Black promotion
        if piece.color == "dark":
            if self.game_mode.get() == "1v1":
                popup = Toplevel(self)
                popup.title("Choose the piece")
                popup.grab_set()

                def choose_piece_dark(new_piece):
                    piece.piece_type = new_piece
                    piece.load_image(self.title_size)
                    self.board.promotion_pending = None
                    self.board.turn = "light"
                    popup.destroy()
                    self.render()

                Button(popup, text="Queen", command=lambda: choose_piece_dark("queen")).pack(pady=2)
                Button(popup, text="Rook", command=lambda: choose_piece_dark("rook")).pack(pady=2)
                Button(popup, text="Bishop", command=lambda: choose_piece_dark("bishop")).pack(pady=2)
                Button(popup, text="Knight", command=lambda: choose_piece_dark("knight")).pack(pady=5)
                return
            else:
                piece.piece_type = "queen"
                piece.load_image(self.title_size)
                self.board.promotion_pending = None
                self.board.turn = "light"
                self.render()
                return

        popup = Toplevel(self)
        popup.title("Choose the piece")
        popup.grab_set()

        def choose_piece(new_piece):
            piece.piece_type = new_piece
            piece.load_image(self.title_size)
            self.board.promotion_pending = None
            self.board.turn = "dark"
            popup.destroy()
            self.render()

            self.after(500, self.execute_ai_move)

        queen_button = Button(popup, text="Queen", command=lambda: choose_piece("queen"))
        rook_button = Button(popup, text="Rook", command=lambda: choose_piece("rook"))
        bishop_button = Button(popup, text="Bishop", command=lambda: choose_piece("bishop"))
        knight_button = Button(popup, text="Knight", command=lambda: choose_piece("knight"))

        queen_button.pack(pady=2)
        rook_button.pack(pady=2)
        bishop_button.pack(pady=2)
        knight_button.pack(pady=5)

    def update_controls(self):
        if self.board.game_started:
            self.ai_menu.config(state="disabled")
        else:
            self.ai_menu.config(state="normal")

    def render(self):
        self.update_controls()
        self.canvas.delete("all")
        self.draw_board()

        if self.board.selected is not None:
            row, col = self.board.selected
            x1 = col * self.title_size
            x2 = x1 + self.title_size
            y1 = row * self.title_size
            y2 = y1 + self.title_size
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="#F6F669", outline="")

        for r, c in self.board.legal_moves:
            x1 = c * self.title_size
            x2 = x1 + self.title_size
            y1 = r * self.title_size
            y2 = y1 + self.title_size
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="#CDD16E", outline="")
        
        self.draw_pieces()
        self.history_box.config(state="normal")
        self.history_box.delete("1.0", "end")
        for i, (f, t) in enumerate(self.board.move_history):
            self.history_box.insert("end", f"{i+1}. {f} → {t}\n")
        self.history_box.config(state="disabled")

        if self.board.promotion_pending is not None:
            self.show_promotion()

        if self.board.status != "playing":
            if "checkmate" in self.board.status:
                lose = self.board.status.split("_")[1]
                winner = "Dark (AI)" if lose == "light" else "Light (Player)"
                messagebox.showinfo("Game Over", f"Checkmate! The winner is {winner}!")
            elif self.board.status == "stalemate":
                messagebox.showinfo("Game Over", "Stalemate! The game ends with draw.")

    def tick_time(self):
        if self.board.status != "playing":
            return
        
        self.timing.tick()
        self.light_timer_label.config(text= f"Light: {self.timing.get_display("light")}")
        self.dark_timer_label.config(text= f"Dark: {self.timing.get_display("dark")}")

        if self.timing.is_timeout("light"):
            self.board.status = "game_over"
            messagebox.showinfo("Game Over", f"Timeout, Dark wins!")
            return
        
        if self.timing.is_timeout("dark"):
            self.board.status = "game_over"
            messagebox.showinfo("Game Over", f"Timeout, Light wins!")
            return
        
        self.after(1000, self.tick_time)

app = ChessApp()
app.mainloop()