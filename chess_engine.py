import copy
import algorithm_utils
from select import select
from shutil import move
from utils import diagonalDirections, kingDirections, knightDirections, straightDirections



class Move(object):
    rank_to_row = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    row_to_rank = {v: k for k, v in rank_to_row.items()}
    file_to_col = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    col_to_file = {v: k for k, v in file_to_col.items()}

    def __init__(self, start_square, end_sq, board, is_enpassant_move=False, is_castle_move=False):
        self.start_row = start_square[0]
        self.start_col = start_square[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        self.piece_mmove = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        self.is_pawm_promotion = (self.piece_mmove == "wp" and self.end_row == 0) or (self.piece_mmove == "bp" and self.end_row == 7)
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = "wp" if self.piece_mmove == "bp" else "bp"
        self.is_castle_move = is_castle_move
        self.is_capture = (self.piece_captured != "--")
        self.move_id = self.start_col * 1000 + self.start_row * 100 + self.end_col * 10 + self.end_row

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False

    def get_chess_notation(self):
        return self.get_file_rank(self.start_row, self.start_col) + self.get_file_rank(self.end_row, self.end_col)
    def get_file_rank(self, row, col):
        return str(self.col_to_file[col] + self.row_to_rank[row])

    def __str__(self):
        #castleMove:
        if self.is_castle_move:
            return "O-O" if self.end_col == 6 else "O-O-O"
        end_square = self.get_file_rank(self.end_row, self.end_col)
        #pawn move
        if self.piece_mmove[1] == 'p':
            if self.is_capture:
                return self.col_to_file[self.start_col] + "x" + end_square
            else:
                return end_square

        #piece moves
        move_string = self.piece_mmove[1]
        if self.is_capture:
            move_string += "x"
        return move_string + end_square
    
    
class GameState():
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        self.move_functions = {'p': self._get_pawn_moves, 'R': self._get_rook_moves, 'N': self._get_knight_moves,
                              'B': self._get_bishop_moves, 'Q': self._get_queen_moves, 'K': self._get_king_moves}
        self.white_to_move = True
        self.moves_log: list[Move] = []
        self.white_king_locate = (7, 4)
        self.black_king_locate = (0, 4)
        self.in_check = False
        self.check_mate = False
        self.stale_mate = False
        self.enpassant_possible = ()
        self.enpassant_possible_log = [self.enpassant_possible]
        self.pins = []
        self.checks = []
        self.current_castling_right = castleRight(True, True, True, True)
        self.castle_rights_log = [castleRight(self.current_castling_right.wks, self.current_castling_right.wqs,
                                            self.current_castling_right.bks, self.current_castling_right.bqs)]


    def make_move(self, move: Move):
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_mmove
        self.moves_log.append(move)
        self.white_to_move = not self.white_to_move
        if move.piece_mmove == "wK":
            self.white_king_locate = (move.end_row, move.end_col)
        if move.piece_mmove == "bK":
            self.black_king_locate = (move.end_row, move.end_col)
        # promotion
        if move.is_pawm_promotion:
            piecePromote = 'Q' #input("Promote R, N, B, Q: ")
            #piecePromote = piecePromote.upper()
            self.board[move.end_row][move.end_col] = move.piece_mmove[0] + piecePromote
        # Enpassant Move
        if move.is_enpassant_move:
            self.board[move.start_row][move.end_col] = "--"  # capturing the pawn
        # EnpassantPossible update
        if move.piece_mmove[1] == 'p' and (abs(move.start_row - move.end_row) == 2):  # only 2 squares pawn move
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.end_col)
        else:
            self.enpassant_possible = ()  # not en passant move
        self.enpassant_possible_log.append(self.enpassant_possible)
        # update castling right - whenever king move or rook move
        self.update_castle_right(move)
        self.castle_rights_log.append(castleRight(self.current_castling_right.wks, self.current_castling_right.wqs,
                                                self.current_castling_right.bks, self.current_castling_right.bqs))
        # castle move
        if move.is_castle_move:
            if move.end_col-move.start_col == 2:
                self.board[move.end_row][move.end_col-1] = self.board[move.end_row][move.end_col+1]
                self.board[move.end_row][move.end_col+1] = "--"
            else:
                self.board[move.end_row][move.end_col+1] = self.board[move.end_row][move.end_col-2]
                self.board[move.end_row][move.end_col-2] = "--"



    def undo_move(self):
        if len(self.moves_log) != 0:
            move = self.moves_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_mmove
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move
            if move.piece_mmove == "wK":
                self.white_king_locate = (move.start_row, move.start_col)
            if move.piece_mmove == "bK":
                self.black_king_locate = (move.start_row, move.start_col)
        #undo enpassant move
            if move.is_enpassant_move:
                self.board[move.end_row][move.end_col] = "--"
                self.board[move.start_row][move.end_col] = move.piece_captured

            self.enpassant_possible_log.pop()
            self.enpassant_possible = copy.deepcopy(self.enpassant_possible_log[-1])
        #undo castling right
            self.castle_rights_log.pop()
            self.current_castling_right = copy.deepcopy(self.castle_rights_log[-1])
        #undo castle move
            if move.is_castle_move:
                if move.end_col - move.start_col == 2:
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = "--"
                else:
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = "--"

            self.check_mate = False
            self.stale_mate = False

    def update_castle_right(self, move: Move):
        if move.piece_mmove == "wK":
            self.current_castling_right.wks = False
            self.current_castling_right.wqs = False
        elif move.piece_mmove == "bK":
            self.current_castling_right.bks = False
            self.current_castling_right.bqs = False
        elif move.piece_mmove == "wR":
            if move.start_row == 7:
                if move.start_col == 0:
                    self.current_castling_right.wqs = False
                elif move.start_col == 7:
                    self.current_castling_right.wks = False
        elif move.piece_mmove == "bR":
            if move.start_row == 0:
                if move.start_col == 0:
                    self.current_castling_right.bqs = False
                elif move.start_col == 7:
                    self.current_castling_right.bks = False

        if move.piece_captured == 'wR':
            if move.end_row == 7:
                if move.end_col == 0:
                    self.current_castling_right.wqs = False
                elif move.end_col == 7:
                    self.current_castling_right.wks = False
        elif move.piece_captured == 'bR':
            if move.end_row == 0:
                if move.end_col == 0:
                    self.current_castling_right.bqs = False
                elif move.end_col == 7:
                    self.current_castling_right.bks = False
            


    def get_valid_moves(self):
        moves = []
        self.in_check, self.pins, self.checks = self.check_for_pins_and_checks()
        if self.white_to_move:
            kingRow = self.white_king_locate[0]
            kingCol = self.white_king_locate[1]
        else:
            kingRow = self.black_king_locate[0]
            kingCol = self.black_king_locate[1]

        if self.in_check:
            if len(self.checks) == 1:
                moves = self.get_all_possible_moves()
                check = self.checks[0]
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][check_col]
                valid_sqs = []
                if piece_checking[1] == 'N':
                    valid_sqs = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_sq = (kingRow + check[2] * i, kingCol + check[3] * i)
                        valid_sqs.append(valid_sq)
                        if valid_sq[0] == check_row and valid_sq[1] == check_col:
                            break
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].piece_mmove[1] != 'K':
                        if not (moves[i].end_row, moves[i].end_col) in valid_sqs:
                            moves.remove(moves[i])
            else:
                self._get_king_moves(kingRow, kingCol, moves)
        else:
            moves = self.get_all_possible_moves()

        if len(moves) == 0:
            if self.in_check:
                self.check_mate = True
            else:
                self.stale_mate = True

        return moves


    def get_all_possible_moves(self):
        moves = []
        for r in range(8):
            for c in range(8):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.white_to_move) or (turn == 'b' and not self.white_to_move):
                    piece = self.board[r][c][1]
                    self.move_functions[piece](r, c, moves)
        return moves

    def _get_pawn_moves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        
        if self.white_to_move:
            kingRow = self.white_king_locate[0]
            kingCol = self.white_king_locate[1]
        else:
            kingRow = self.black_king_locate[0]
            kingCol = self.black_king_locate[1]
        if self.white_to_move:
            if self.board[r-1][c] == "--":
                if not piecePinned or pinDirection == (-1, 0):
                    moves.append(Move((r, c), (r-1, c), self.board))
                    if r == 6:
                        if self.board[4][c] == "--":
                            moves.append(Move((r, c), (4, c), self.board))
            if c-1 >= 0:
                if self.board[r-1][c-1][0] == "b":
                    if not piecePinned or pinDirection == (-1, -1):
                        moves.append(Move((r, c), (r-1, c-1), self.board))
                elif (r-1, c-1) == self.enpassant_possible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:
                            insideRange = range(kingCol + 1, c-1)
                            outsideRange = range(c+1, 8)
                        else:
                            insideRange = range(kingCol - 1, c, -1)
                            outsideRange = range(c-2, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != "--":
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == 'b' and (square[1] == 'R' or square[1] == 'Q'):
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r - 1, c - 1), self.board, is_enpassant_move=True))
            if c+1 <= 7:
                if self.board[r-1][c+1][0] == "b":
                    if not piecePinned or pinDirection == (-1, 1):
                        moves.append(Move((r, c), (r-1, c+1), self.board))
                elif (r-1, c+1) == self.enpassant_possible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:
                            insideRange = range(kingCol + 1, c)
                            outsideRange = range(c+2, 8)
                        else:
                            insideRange = range(kingCol - 1, c+1, -1)
                            outsideRange = range(c-1, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != "--":
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == 'b' and (square[1] == 'R' or square[1] == 'Q'):
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r-1, c+1), self.board, is_enpassant_move=True))
        else:
            if self.board[r+1][c] == "--":
                if not piecePinned or pinDirection == (1, 0):
                    moves.append(Move((r, c), (r+1, c), self.board))
                    if r == 1:
                        if self.board[3][c] == "--":
                            moves.append(Move((r, c), (3, c), self.board))
            if c-1 >= 0:
                if self.board[r+1][c-1][0] == "w":
                    if not piecePinned or pinDirection == (1, -1):
                        moves.append(Move((r, c), (r+1, c-1), self.board))
                elif (r+1, c-1) == self.enpassant_possible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:
                            insideRange = range(kingCol + 1, c-1)
                            outsideRange = range(c+1, 8)
                        else:
                            insideRange = range(kingCol - 1, c, -1)
                            outsideRange = range(c-2, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != "--":
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == 'w' and (square[1] == 'R' or square[1] == 'Q'):
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r+1, c-1), self.board, is_enpassant_move=True))

            if c+1 <= 7:
                if self.board[r+1][c+1][0] == "w":
                    if not piecePinned or pinDirection == (1, 1):
                        moves.append(Move((r, c), (r+1, c+1), self.board))
                elif (r+1, c+1) == self.enpassant_possible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c:
                            insideRange = range(kingCol + 1, c)
                            outsideRange = range(c+2, 8)
                        else:
                            insideRange = range(kingCol - 1, c+1, -1)
                            outsideRange = range(c-1, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != "--":
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == 'w' and (square[1] == 'R' or square[1] == 'Q'):
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r+1, c+1), self.board, is_enpassant_move=True))

    def _get_rook_moves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != 'Q':
                    self.pins.remove(self.pins[i])
                break

        enemyColor = 'b' if self.white_to_move else 'w'
        for d in straightDirections:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if (0 <= end_row < 8) and (0 <= end_col < 8):
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[end_row][end_col]
                        if endPiece == "--":
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                            break
                        else:
                            break
                else:
                    break

    def _get_knight_moves(self, r, c, moves):
        piecePinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break

        allyColor = 'w' if self.white_to_move else 'b'
        for d in knightDirections:
            end_row = r + d[0]
            end_col = c + d[1]
            if (0 <= end_row < 8) and (0 <= end_col < 8):
                if not piecePinned:
                    endPiece = self.board[end_row][end_col]
                    if endPiece[0] != allyColor:
                        moves.append(Move((r, c), (end_row, end_col), self.board))

    def _get_bishop_moves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        enemyColor = 'b' if self.white_to_move else 'w'
        for d in diagonalDirections:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if (0 <= end_row < 8) and (0 <= end_col < 8):
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[end_row][end_col]
                        if endPiece == "--":
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                        elif endPiece[0] == enemyColor:
                            moves.append(Move((r, c), (end_row, end_col), self.board))
                            break
                        else:
                            break
                else:
                    break

    def _get_queen_moves(self, r, c, moves):
        self._get_rook_moves(r, c, moves)
        self._get_bishop_moves(r, c, moves)

    def _get_king_moves(self, r, c, moves):
        
        allyColor = 'w' if self.white_to_move else 'b'
        for i in range(8):
            end_row = r + kingDirections[i][0]
            end_col = c + kingDirections[i][1]
            if (0 <= end_row < 8) and (0 <= end_col < 8):
                endPiece = self.board[end_row][end_col]
                if endPiece[0] != allyColor:
                    # place king on the end of square to check
                    if allyColor == 'w':
                        self.white_king_locate = (end_row, end_col)
                    else:
                        self.black_king_locate = (end_row, end_col)
                    inCheck, pins, checks = self.check_for_pins_and_checks()
                    if not inCheck:
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    # place king back
                    if allyColor == 'w':
                        self.white_king_locate = (r, c)
                    else:
                        self.black_king_locate = (r, c)
        self._get_caslte_moves(r, c, moves, allyColor)

    def check_for_pins_and_checks(self):
        pins = []
        checks = []
        inCheck = False
        if self.white_to_move:
            enemyColor = 'b'
            allyColor = 'w'
            start_row = self.white_king_locate[0]
            start_col = self.white_king_locate[1]
        else:
            enemyColor = 'w'
            allyColor = 'b'
            start_row = self.black_king_locate[0]
            start_col = self.black_king_locate[1]

        directions = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, 1), (1, -1))
        for j in range(len(directions)):
            d = directions[j]
            possiblePins = ()
            for i in range(1, 8):
                end_row = start_row + d[0] * i
                end_col = start_col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    endPiece = self.board[end_row][end_col]
                    if endPiece[0] == allyColor and endPiece[1] != 'K':
                        if possiblePins == ():
                            possiblePins = (end_row, end_col, d[0], d[1])
                        else:
                            break
                    elif endPiece[0] == enemyColor:
                        pieceType = endPiece[1]
                        if (0 <= j <= 3 and pieceType == 'R') or \
                                (4 <= j <= 7 and pieceType == 'B') or \
                                (i == 1 and pieceType == 'p' and ((enemyColor == 'b' and 4 <= j <= 5) or (enemyColor == 'w' and 6 <= j <= 7))) or \
                                (pieceType == 'Q') or (i == 1 and pieceType == 'K'):
                            if possiblePins == ():
                                inCheck = True
                                checks.append((end_row, end_col, d[0], d[1]))
                                break
                            else:
                                pins.append(possiblePins)
                                break
                        else:
                            break
                else:
                    break

        for m in knightDirections:
            end_row = start_row + m[0]
            end_col = start_col + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                endPiece = self.board[end_row][end_col]
                if (endPiece[0] == enemyColor) and (endPiece[1] == 'N'):
                    inCheck = True
                    checks.append((end_row, end_col, m[0], m[1]))
                    break

        return inCheck, pins, checks

    def _get_caslte_moves(self, r, c, moves, allyColor=""):
        if self.in_check:
            return  #can't castle while be checked
        if (self.white_to_move and self.current_castling_right.wks) or (not self.white_to_move and self.current_castling_right.bks):
            self._get_kingside_castle_move(r, c, moves, allyColor)
        if (self.white_to_move and self.current_castling_right.wqs) or (not self.white_to_move and self.current_castling_right.bqs):
            self._get_queenside_castle_move(r, c, moves, allyColor)

    def _get_kingside_castle_move(self, r, c, moves, allyColor=""):
        if self.board[r][c+1] == "--" and self.board[r][c+2] == "--":
            if allyColor == 'w':
                self.white_king_locate = (r, c+1)
            else:
                self.black_king_locate = (r, c+1)
            inCheck1, pins, checks = self.check_for_pins_and_checks()
            if allyColor == 'w':
                self.white_king_locate = (r, c+2)
            else:
                self.black_king_locate = (r, c+2)
            inCheck2, pins, checks = self.check_for_pins_and_checks()
            if allyColor == 'w':
                self.white_king_locate = (r, c)
            else:
                self.black_king_locate = (r, c)

            if not inCheck1 and not inCheck2:
                moves.append(Move((r, c), (r, c+2), self.board, is_castle_move=True))

    def _get_queenside_castle_move(self, r, c, moves, allyColor=""):
        if self.board[r][c - 1] == "--" and self.board[r][c - 2] == "--" and self.board[r][c-3] == "--":
            if allyColor == 'w':
                self.white_king_locate = (r, c-1)
            else:
                self.black_king_locate = (r, c-1)
            inCheck1, pins, checks = self.check_for_pins_and_checks()
            if allyColor == 'w':
                self.white_king_locate = (r, c-2)
            else:
                self.black_king_locate = (r, c-2)
            inCheck2, pins, checks = self.check_for_pins_and_checks()
            if allyColor == 'w':
                self.white_king_locate = (r, c-3)
            else:
                self.black_king_locate = (r, c-3)
            inCheck3, pins, checks = self.check_for_pins_and_checks()
            if allyColor == 'w':
                self.white_king_locate = (r, c)
            else:
                self.black_king_locate = (r, c)

            if not inCheck1 and not inCheck2 and not inCheck3:
                moves.append(Move((r, c), (r, c-2), self.board, is_castle_move=True))

class castleRight():
    def __init__(self, wks, wqs, bks, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


