import os
import chess
import chess.pgn
import random
import time
import pickle
import datetime
import time
import shutil
import rep

########
# misc #
########

# path to data directory
rep_path = "Repertoires"

def represents_int(string):
    try: 
        int(string)
        return True
    except ValueError:
        return False

# checks whether a string is a legal move in uci notation
def is_valid_uci(string,board) :
    validity = False
    for move in board.legal_moves :
        if (string == move.uci()) :
            validity = True
            break
    return validity

############
# printing #
############

# `clears' the screen
def clear() :
    for x in range(40) :
        print("")

# prints the side to move
def print_turn(board) :
    print("")
    if (board.turn) :
        print("WHITE to play.")
    else :
        print("BLACK to play.")

# pretty prints the board
def print_board(board,player) :
    string = board.unicode(invert_color = True, empty_square = ".")
    print("")
    if (player) :
        print(string)
    else :
        for row in range(8) :
            row_string = ""        
            for column in range(15) :
                row_string += string[(7-row) * 16 + (14 - column)]
            print(row_string)            
            
        
# prints repertoire moves for the given node
def print_moves(node) :
    if (node.player_to_move) :
        if (node.is_end()) :
            print("\nNo solutions.")
        else :
            print("\nSolutions:")
            for solution in node.variations :
                print(solution.move.uci())
    else :
        if (node.is_end()) :
            print("\nNo problems.")
        else :
            print("\nProblems:")
            for problem in node.variations :
                print(problem.move.uci())

###########################################
# creating / saving / opening repertoires #
###########################################

def rpt_path(name) :
    return rep_path + "/" + name + ".rpt"

def rpt_name(filename) :
    return filename[:-4]

def delete_repertoire(filenames) :
    # TODO: the prompting should go in the calling function
    command = input("\nID to delete:")
    if (represents_int(command) and 1 <= int(command) <= len(filenames)) :
        index = int(command) - 1
        print (f"you are about to permanently delete `{filenames[index]}'.")
        check = input("are you sure:")
        if (check == "y") :
            os.remove(rep_path + "/" + filenames[index])

def save_repertoire (repertoire) :
    filename = rpt_path(repertoire.meta.name)
    update(repertoire)
    with open(filename, "wb") as file :
        pickle.dump(repertoire,file)

def open_repertoire (filename) :
    filepath = rep_path + "/" + filename
    with open(filepath, "rb") as file :
        repertoire = pickle.load(file)
    update(repertoire)
    return repertoire

def update(repertoire) :
    learning_date = repertoire.meta.learning_data[0]
    learning_value = repertoire.meta.learning_data[1]
    max_value = repertoire.meta.learn_max
    today = datetime.date.today()
    # only normalise if today is a new day
    # normalise by the maximum value
    if (learning_date < today) :
        repertoire.meta.learning_data[0] = today
        repertoire.meta.learning_data[1] = 0
        normalise(repertoire,max_value)
    else :
        learning_threshold = max_value - learning_value
        normalise(repertoire,learning_threshold)

##############
# statistics #
##############

def get_scheduled_counts(node) :
    full_counts = get_counts(node)
    return [full_counts[0],full_counts[1]+full_counts[2],full_counts[5]]

def get_counts(node) :
    # new first second review inactive due reachable total
    counts = [0,0,0,0,0,0,0]
    if (node.training) :
        status = node.training.status
        due_date = node.training.due_date
        # first five counts' statuses are handled as integers
        for index in range(5) :
            if (status == index) :
                counts[index] += 1
        # due count
        if (status == rep.REVIEW and due_date <= datetime.date.today()) :
            counts[5] += 1
        # increment reachable count
        counts[6] += 1

    # recursive part
    if (not node.is_end()) :
        if (node.player_to_move) :
            # search only the main variation
            child_counts = get_counts(node.variations[0])
            for index in range(7) :
                counts[index] += child_counts[index]
        else :
            # search all variations
            for child in node.variations :
                child_counts = get_counts(child)
                for index in range(7) :
                    counts[index] += child_counts[index]

    return counts

def get_total_count(node) :
    if (node.training) :
        count = 1
    else :
        count = 0
    if (not node.is_end()):
        for child in node.variations :
            count += get_total_count(child)                    
    return count


        
#############
# main menu #
#############

def main_menu():
    command = ""
    while(command != "q") :
        filenames = os.listdir(rep_path)    
        clear()
        print_main_overview(filenames)
        print_main_options(filenames)
        command = (input("\n:"))
        
        if (represents_int(command) and 1 <= int(command) <= len(filenames)) :
            index = int(command) - 1
            repertoire_menu(filenames[index])
        elif (command == "n") :
            new_repertoire()
        elif (command == "d" and len(filenames) != 0) :
            delete_repertoire(filenames)

def print_main_overview(filenames) :

    name_width = 20

    if (len(filenames) == 0) :
        print("You currently have no repertoires.")
        return

    # print header
    header = "ID".ljust(3) + "COV.".ljust(5) + "NAME".ljust(name_width)
    header += "WAITING".ljust(9) + "LEARNED".ljust(9)
    header += "UNSEEN".ljust(8) + "TOTAL".ljust(6)
    print(header)

    
    
    # print the stats for each repertoire
    for index, filename in enumerate(filenames) :
        repertoire = open_repertoire(filename)
        counts = get_counts(repertoire)
        id = index + 1
        if (counts[6] != 0) :
            coverage = int(round(counts[3] / counts[6] * 100))
        waiting = counts[0] + counts[1] + counts[2] + counts[5]
        learned = counts[3]
        unseen = counts[4]
        total = counts[6]
        info = str(id).ljust(3)
        if (counts[6] != 0) :
            info += (str(coverage) + "% ").rjust(5)
        else :
            info += "".ljust(5)
        info += str(repertoire.meta.name).ljust(name_width)
        info += str(waiting).ljust(9)
        info += str(learned).ljust(9)
        info += str(unseen).ljust(8)
        info += str(total).ljust(7)
        print(info)

def print_main_options(filenames) :
    print ("")
    if (len(filenames) != 0) :
        print("[ID] select")
    print("'n' new")
    if (len(filenames) != 0) :
        print("'d' delete")
    print("'q' quit")

############
# new menu #
############

# creates a new repertoire
def new_repertoire() :
    
    # get user choices
    board = get_starting_position()
    if (board == "CLOSE") :
        return
    clear()
    print_board(board,True)
    colour = input("\nYou play as:\n'w' for White\n'b' for Black\n\n:")
    while (colour != "b" and colour != "w"):
        colour = input(":")
    player = colour == "w"
    name = input("\nName:")
    while (os.path.exists(rpt_path(name))) :
        name = input("That name is taken.\nChoose another:")

    # create the repertoire
    rpt = chess.pgn.Game()
    rpt.setup(board)
    rpt.meta = rep.MetaData(name, player)
    rpt.training = False
    rpt.player_to_move = player == board.turn
    save_repertoire(rpt)
    clear()
    print(f"Repertoire {name} created.")

# TODO - rewrite this function into the current style
# prompts user to choose starting position
def get_starting_position() :
    board = chess.Board()
    while(True) :
        clear()
        print("\nChoose starting position.")
        print_board(board,True)
        print("\nEnter a move or hit [Enter] to select this position.")
        print("'b' to go back one move")
        print("'c' to close.")
        uci = input("\n:")

        if (uci == "c") :
            return "CLOSE"
        elif (uci == "b") :
            try:
                board.pop()
            except IndexError:
                print("Cannot go back from root position.")
        elif (is_valid_uci(uci,board)) :
            board.push(chess.Move.from_uci(uci))
        elif (uci == "") :
            return board

###################
# repertoire menu #
###################

# displays the overview of the given repertoire `name'

def repertoire_menu(filename) :
    command = ""
    while(command != "c") :
        repertoire = open_repertoire(filename)
        counts = get_counts(repertoire)
        clear()
        print_repertoire_overview(repertoire,counts)
        print_repertoire_options(repertoire,counts)
        command = input("\n:")
        if (command == "m") :
            manage(filename)
        elif (command == "t") :
            train(filename)

def print_repertoire_overview(repertoire,counts) :
    # setup
    tag_width = 14
    if (counts[0] + counts[1] + counts[2] + counts[5] > 0) :
        status_msg = "training available"
    else :
        status_msg = "up to date"
    
    # print header
    print("Repertoire: " + repertoire.meta.name)
    print("Status    : " + status_msg)

    # print sceduled counts
    print("")
    print("New".ljust(tag_width) + str(counts[0]))
    print("Learning".ljust(tag_width) + str(counts[1] + counts[2]))
    print("Due".ljust(tag_width) + str(counts[5]))

    # print remaining counts    
    total = get_total_count(repertoire)
    print("")
    print("In review".ljust(tag_width) + str(counts[3]))
    print("Inactive".ljust(tag_width) + str(counts[4]))
    print("Reachable".ljust(tag_width) + str(counts[6]))
    print("Total".ljust(tag_width) + str(total))

def print_repertoire_options(repertoire,counts) :
    status = repertoire.meta.status
    print("\n'm' manage")
    if (counts[0] + counts[1] + counts[2] + counts[5] > 0) :
        print("\n't' train")
    print("'c' close")

###############
# manage menu #
###############

# user management of repertoire as a pgn
def manage(filename):
    repertoire = open_repertoire(filename)
    player = repertoire.meta.player
    board = repertoire.board()
    node = repertoire        

    command = ""
    while(command != "c") :

        clear()
        print_node_overview(node,player,board)
        print_node_options(node)
        command = input("\n:")
        if (command == "b" and node.parent != None) :
            node = node.parent
            board.pop()
        elif (command == "d" and len(node.variations) != 0) :
            delete_move(node,board)
            
        elif (command == "p" and len(node.variations) > 1) :
            promote_move(node,board)
            
        elif (is_valid_uci(command,board)) :
            move = chess.Move.from_uci(command)
            if (not node.has_variation(move)) :
                add_move(node,move)
            node = node.variation(move)
            board.push(move)

    #threshold = compute_learning_threshold(repertoire)
    #normalise(repertoire,)
    save_repertoire(repertoire)    
    clear()
    print(f"Saved {rpt_name(filename)}.")

"""
def compute_learning_threshold(repertoire) :
    learning_date = 
    learned_today = repertoire.meta.num_new_learned[1]
    if (datetime.date.today() == repertoire.meta.num_new_learned[0]) :
        learned_today = 
"""
def print_node_overview(node,player,board) :
    print_turn(board)
    print_board(board,player)
    print_moves(node)

def print_node_options(node) :
    print("")
    if (node.parent != None) :
        print("'b' back")
    if (not node.is_end()) :
        print("'d' delete")
    if (len(node.variations) > 1) :
        print("'p' promote")
    print ("'c' close")
    print ("<move> enter move")

def delete_move(node,board) :
    command = input("delete move:")
    if (is_valid_uci(command,board)) :
        move = chess.Move.from_uci(command)
        if (node.has_variation(move)) :
            print(f"You are about to permanently delete the move '{command}'.")
            command = input("are you sure:")
            if (command == "y") :
                node.remove_variation(move)

def promote_move(node,board) :
    command = input("promote move:")
    if (is_valid_uci(command,board)) :
        move = chess.Move.from_uci(command)
        if (node.has_variation(move)) :
            node.promote(move)

def add_move(node,move) :
    new_node = node.add_variation(move)
    new_node.player_to_move = not node.player_to_move
    if (node.parent == None or new_node.player_to_move) :
        new_node.training = False        
    else :
        new_node.training = rep.TrainingData()

# sets the card statuses based on the current environment
        
def normalise(node,threshold) :
    # configure training data
    if (node.training) :
        if (threshold <= 0) :
            for status in [rep.NEW,rep.FIRST_STEP,rep.SECOND_STEP] :
                if (node.training.status == status) :
                    node.training.status = rep.INACTIVE
        else : # threshold exceeds 0
            if (node.training.status == rep.INACTIVE) :
                node.training.status = rep.NEW
            for status in [rep.NEW,rep.FIRST_STEP,rep.SECOND_STEP] :
                if (node.training.status == status) :
                    threshold -= 1

    if (not node.is_end()) :
        if (node.player_to_move) : # call all children recursively
            threshold = normalise(node.variations[0],threshold)
        else : # call only the main variation
            for child in node.variations :
                threshold = normalise(child,threshold)
                
    return threshold

##############
# train menu #
##############

def train(filename):
    repertoire = open_repertoire(filename)
    player = repertoire.meta.player
    board = repertoire.board()
    node = repertoire        

    # generate queue
    queue = generate_training_queue(repertoire,board)
    # play queue

    command = ""
    while(len(queue) != 0) :
        card = queue.pop(0)
        counts = get_counts(repertoire)
        clear()
        print(f"{counts[0]} {counts[1]} {counts[2]} {counts[5]}")
        result = play_card(card,repertoire)
        if (result == "CLOSE") :
            break
        handle_card_result(result,card,queue,repertoire)

    # save and quit trainer
    save_repertoire(repertoire)

def play_card(card,repertoire) :
    root = card[0]
    node = card[1]
    status = node.training.status
    player = repertoire.meta.player

    # front of card
    front = root.variations[0]
    if (status == 0) :
        print("\nNEW : this is a position you haven't seen before")
    if (status == 1 or status == 2) :
        print("\nLEARNING : this is a position you're currently learning")
    if (status == 3) :
        print("\nRECALL : this is a position you've learned, due for recall")

    print_board(front.board(),player)
    if (status == 0) :
        print("\nGuess the move..")
    else :
        print("\nRecall the move..")
    print(".. then hit [enter] or 'c' to close")
    uci = input("\n:")
    if (uci == "c") :
        return "CLOSE"

    # back of card
    back = front.variations[0]
    clear()    
    print("Solution:")
    print_board(back.board(),player)

    if (status == 0) :
        print("\nHit [enter] to continue.")
        input("\n\n:")
    if (status != 0) :
        print("\n'h' hard    [enter] ok    'e' easy\n")
        uci = input("\n:")
   
    while (True) :
        if (uci == "e") :
            return "EASY"
        if (uci == "h") :
            return "HARD"
        if (uci == "") :
            return "OK"
        if (uci == "c") :
            return "CLOSE"
        uci = input(":")
        
        
def handle_card_result(result,card,queue,repertoire) :
    root = card[0]
    node = card[1]
    status = node.training.status
    
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    
    if (status == rep.NEW) :
        print("Here")
        node.training.status = rep.FIRST_STEP
        increase = int(round(3 * random.random()))
        offset = min(1 + increase,len(queue))
        queue.insert(offset,card)
                    
    elif (status == rep.FIRST_STEP) :
        if (result == "EASY") :
            node.training.status = rep.REVIEW
            node.training.last_date = today
            node.training.due_date = tomorrow
            repertoire.meta.learning_data[1] += 1
        elif (result == "OK") :
            node.training.status = rep.SECOND_STEP
            increase = int(round(3 * random.random()))
            offset = min(6 + increase,len(queue))
            queue.insert(offset,card)
        elif (result == "HARD") :
            node.training.status = rep.FIRST_STEP            
            increase = int(round(3 * random.random()))
            offset = min(1 + increase,len(queue))
            queue.insert(offset,card)

    elif (status == rep.SECOND_STEP) :
        if (result == "EASY") :
            node.training.status = rep.REVIEW
            node.training.last_date = today
            node.training.due_date = today + datetime.timedelta(days=3)
            repertoire.meta.learning_data[1] += 1
        elif (result == "OK") :
            node.training.status = rep.REVIEW
            node.training.last_date = today
            node.training.due_date = tomorrow
            repertoire.meta.learning_data[1] += 1
        elif (result == "HARD") :
            node.training.status = rep.FIRST_STEP            
            increase = int(round(3 * random.random()))
            offset = min(1 + increase,len(queue))
            queue.insert(offset,card)
            
    elif (status == rep.REVIEW) :
        previous_gap = (node.training.due_date - node.training.last_date).days

        if (result == "HARD") :
            node.training.status = rep.FIRST_STEP
            offset = min(2,len(queue))
            queue.insert(offset,card)
            repertoire.meta.learning_data[1] -= 1

        else :
            if (result == "EASY") :
                multiplier = 3 + random.random()
            else :
                multiplier = 2 + random.random()
            new_gap = int(round(previous_gap * multiplier))
            node.training.status = rep.REVIEW
            node.training.last_date = today
            node.training.due_date = today + datetime.timedelta(days=new_gap)

def generate_training_queue(node,board) :
    # the board must be returned as it was given
    queue = []    
    
    if (node.training) :
        status = node.training.status
        due_date = node.training.due_date
        today = datetime.date.today()
        if (status == 0 or status == 1 or status == 2 or (status == 3 and due_date <= today)) :
                # add a card to the queue
            solution = board.pop()
            problem = board.pop()
            game = chess.pgn.Game()
            game.setup(board)
            new_node = game.add_variation(problem)
            new_node = new_node.add_variation(solution)
            board.push(problem)
            board.push(solution)
            queue.append([game,node])

    # recursive part
    if (not node.is_end()) :
        if (node.player_to_move) :
            # search only the main variation
            child = node.variations[0]
            board.push(child.move)
            queue += generate_training_queue(child,board)
            board.pop()

        else :
            # search all variations
            for child in node.variations :
                board.push(child.move)
                queue += generate_training_queue(child,board)
                board.pop()

    return queue

    
############### 
# entry point #
###############

main_menu()


# temp copied code

"""        
    node = game
    board = node.board()
    player = board.turn

    result = query_node(node)
    
    while (result != "SAVE") :
        if (result == "BACK") :
            if (node != game) :
                node = node.parent
                
        elif (result == "DELETE") :
            uci = input("delete move:")
            if (is_valid_uci(uci,node.board())) :
                move = chess.Move.from_uci(uci)
                if (node.has_variation(move)) :
                    node.remove_variation(move)

        elif (result == "PROMOTE") :
            uci = input("promote move:")
            if (is_valid_uci(uci,node.board())) :
                move = chess.Move.from_uci(uci)
                if (node.has_variation(move)) :
                    node.promote_to_main(move)
                           
        elif (result != "INVALID") :
            move = chess.Move.from_uci(result)
            if (not node.has_variation(move)) :
                node.add_main_variation(move)
            node = node.variation(move)
            board = node.board()                        

        result = query_node(node)
"""

def folder_path(name) :
    return data_path + name + "/"
def pgn_path(name) :
    return folder_path(name) + name + ".pgn"
failure_string = " "

data_path = "Repertoires/"

##########
# load() #
##########

# loads a saved repertoire
# checks that the file exists and can be opened as a pgn by python-chess
# return the path to the loaded repertoire file
def load() :
    clear()
    file_path = input("filename:")
    try:
        pgn = open(file_path, "r")
    except:
        clear()
        print("\nFile error.")
        return
    repertoire = chess.pgn.read_game(pgn)
    pgn.close()
    clear()
    print("Loaded repertoire `" + str(file_path) + "'.")
    return file_path


# returns the parsed repertoire from its file path
def get_pgn_game(repertoire) :
    game = chess.pgn.read_game(repertoire.pgn)
    return game

def is_candidate(node,player) :
    return (node.board().turn == player and node.parent != None)

def is_response(node,player) :
    return (node.board().turn != player and node.parent != None)

# tells you whether a training node is the last training node in that line

def is_leaf(training_node) :
    if (training_node.is_end()) :
        return True
    for child in training_node.variations :
        if (not child.is_end()) :
            return False
    return True

# returns the set of responses at or deeper than the given node
def get_responses(node,root) :
    responses = []
    if (is_response(node,root)) :
        responses.append(node)
    if (not node.is_end()) :
        for child in node.variations :
            responses += get_responses(child,root)
    return responses

# returns repertoire name from repertoire filepath (wrt rep_path)

def get_full_counts(node) :
    counts = [0,0,0,0,0]
    if (node.training) :
        status = node.training.status
        if (status == rep.NEW) :
            counts[0] += 1
        elif (status == rep.FIRST_STEP) :
            counts[1] += 1
        elif (status == rep.SECOND_STEP) :
            counts[2] += 1
        elif (status == rep.REVIEW) :
            counts[3] += 1
        elif (status == rep.INACTIVE) :
            counts[4] += 1

    for child in node.variations :
        child_counts = get_full_counts(child)
        for index in range(5) :
            counts[index] += child_counts[index]

    return counts
