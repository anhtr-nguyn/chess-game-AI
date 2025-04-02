import random
import time


pieceScore = {"K": 0, "Q": 90, "R": 50, "B": 35, "N": 30, "p": 10}

knightScore =  [[1, 1, 1, 1, 1, 1, 1, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 1, 1, 1, 1, 1, 1, 1]]

bishopScore =  [[4, 3, 2, 1, 1, 2, 3, 4],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [4, 3, 2, 1, 1, 2, 3, 4]]

queenScore =   [[1, 1, 1, 3, 1, 1, 1, 1],
                [1, 2, 3, 3, 3, 1, 1, 1],
                [1, 4, 3, 3, 3, 4, 2, 1],
                [1, 2, 3, 3, 3, 2, 2, 1],
                [1, 2, 3, 3, 3, 2, 2, 1],
                [1, 4, 3, 3, 3, 4, 2, 1],
                [1, 2, 3, 3, 3, 1, 1, 1],
                [1, 1, 1, 3, 1, 1, 1, 1]]

rookScore =    [[4, 3, 4, 4, 4, 4, 3, 4],
                [4, 4, 4, 4, 4, 4, 4, 4],
                [1, 1, 2, 3, 3, 2, 1, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 1, 2, 3, 3, 2, 1, 1],
                [4, 4, 4, 4, 4, 4, 4, 4],
                [4, 3, 4, 4, 4, 4, 3, 4]]

whitePawnScore =   [[8, 8, 8, 8, 8, 8, 8, 8],
                    [8, 8, 8, 8, 8, 8, 8, 8],
                    [5, 6, 6, 7, 7, 6, 6, 5],
                    [2, 3, 3, 5, 5, 3, 3, 2],
                    [1, 2, 3, 4, 4, 3, 2, 1],
                    [1, 2, 3, 3, 3, 3, 2, 1],
                    [1, 1, 1, 0, 0, 1, 1, 1],
                    [0, 0, 0, 0, 0, 0, 0, 0]]

blackPawnScore =   [[0, 0, 0, 0, 0, 0, 0, 0],
                    [1, 1, 1, 0, 0, 1, 1, 1],
                    [1, 2, 3, 3, 3, 3, 2, 1],
                    [1, 2, 3, 4, 4, 3, 2, 1],
                    [2, 3, 3, 5, 5, 3, 3, 2],
                    [5, 6, 6, 7, 7, 6, 6, 5],
                    [8, 8, 8, 8, 8, 8, 8, 8],
                    [8, 8, 8, 8, 8, 8, 8, 8]]

piecePosScores =  {'N': knightScore, 'B': bishopScore, 'Q': queenScore, 'R': rookScore, "wp": whitePawnScore, "bp": blackPawnScore}


check_mate = 100000
stale_mate = 0
MAX_DEPTH = 4

''' Find random move for AI '''
def findRandomMove(validMoves):
    if len(validMoves) > 0:
        return validMoves[random.randint(0, len(validMoves)-1)]


def findBestMoveMinimax(gs, validMoves):
    global nextMove
    global nodes
    nextMove = None
    alpha = -check_mate
    beta = check_mate
    nodes = 0
    start_time = time.time()
    findMoveMinimax(gs, validMoves, MAX_DEPTH, alpha, beta, gs.white_to_move)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print ("elapsed_time:{0}".format(elapsed_time) + "[sec]")
    print(nodes)
    return nextMove


def findMoveMinimax(gs, validMoves, depth, alpha, beta, white_to_move):
    global nextMove
    global nodes
    nodes += 1
    if depth == 0 or gs.check_mate or gs.stale_mate:
        return scoreBoard(gs)
    random.shuffle(validMoves)
    if white_to_move:
        maxScore = -check_mate
        random.shuffle(validMoves)
        for move in validMoves:
            gs.make_move(move)
            nextMoves = gs.get_valid_moves()
            score = findMoveMinimax(gs, nextMoves, depth - 1, alpha, beta, False)
            gs.undo_move()
            if score > maxScore:
                maxScore = score
                if depth == MAX_DEPTH:
                    nextMove = move
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return maxScore
    else:
        minScore = check_mate
        random.shuffle(validMoves)
        for move in validMoves:
            gs.make_move(move)
            nextMoves = gs.get_valid_moves()
            score = findMoveMinimax(gs, nextMoves, depth - 1, alpha, beta, True)
            gs.undo_move()
            if score < minScore:
                minScore = score
                if depth == MAX_DEPTH:
                    nextMove = move
            beta = min(beta, score)
            if beta <= alpha:
                break
        return minScore

def scoreBoard(gs):
    if gs.check_mate:
        if gs.white_to_move:
            return -check_mate  #black win
        else:
            return check_mate   #white win
    elif gs.stale_mate:
        return stale_mate
    # if not check_mate or stale_mate:
    score = 0
    for row in range(8):
        for col in range(8):
            square = gs.board[row][col]
            if square != "--":
                piecePosScore = 0
                if square[1] != "K":
                    if square[1] == "p":
                        piecePosScore = piecePosScores[square][row][col]
                    else:
                        piecePosScore = piecePosScores[square[1]][row][col]
                if square[0] == 'w':
                    score += pieceScore[square[1]] + piecePosScore
                elif square[0] == 'b':
                    score -= pieceScore[square[1]] + piecePosScore
    return score


