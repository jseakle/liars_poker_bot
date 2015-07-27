#TODO
#Same player can't enter twice

#!/usr/bin/python
import twitter, codecs, datetime, re, keys, random
api = twitter.Api(consumer_key=keys.consumer_key, consumer_secret=keys.consumer_secret, access_token_key=keys.access_token_key, access_token_secret=keys.access_token_secret)


class Card(object):


    def __init__(self, **kwargs):
        self.suit = "G" #generic
        self.rank = 0

        if kwargs.has_key("rank"):
            self.rank = kwargs["rank"]
        if kwargs.has_key("suit"):
            self.suit = kwargs["suit"]

    def __str__(self):
        return str(self.rank) + self.suit

    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

    def __cmp__(self, other):
        return cmp(self.rank, other.rank)

    
class Hand(object):
    
    def __init__(self, cards):
        self.cards = cards

    def __eq__(self, other):
        if other == None:
            return False
        return sorted(self.cards) == sorted(other.cards)

    def __str__(self):
        ret = ""
        for card in self.cards:
            ret += str(card) + ", "
        return ret[:-2]

class Game(object):

    def __init__(self, players, last_tweet="", elimination_threshold=5, hands=[], turn=None, call=None):
        self.players = players #List of player name strings in turn order
        self.last_tweet = last_tweet #String tweet id
        self.elimination_threshold = elimination_threshold
        self.losers = [] #List of player name strings who have lost
        self.hands = hands #List of player Hand objects in turn order
        if hands == []:
            deal_hands(self)
        self.turn = turn if turn != None else players[0] #Player name string
        self.call = call #Hand object


#Resets player hands, giving an additional card to the loser.
def deal_hands(game, loser=None):

    deck = cards[:]
    random.shuffle(deck)

    #New game
    if loser == None: 
        for player in game.players:
            game.hands += [Hand([deck.pop()])]
    #New round
    else:
        loser_index = game.players.index(loser)

        if len(game.hands[loser_index]) == game.elimination_threshold:
            eliminate_player(game.players[loser_index])

        for index, hand in enumerate(game.hands):
            if game.players[index] in game.losers:
                continue

            num_cards = len(hand.cards)
            if index == loser_index:
                num_cards += 1

            cards = []
            for i in xrange(num_cards):
                cards += [deck.pop()]
            game.hands[index] = Hand(cards)

#Eventually this should send a tweet announcing the elimination
def eliminate_player(game, player):

    game.losers.append(player)
                

        
class BadCallException(Exception):

    messages = {
        "parse" : "Please see my bio for instructions.",
        "pair" : "A pair call requires exactly one rank, e.g. 'pair of 5s'.",
        "2pair" : "A two-pair call requires exactly two ranks, e.g. 'two pair, 5s and 6s'.",
        "three" : "A three of a kind call requires exactly one rank, e.g. 'three 5s.'",
        "flush" : "A flush call requires exactly one suit, e.g. 'flush of clubs'.",
        "straight" : "A straight call requires exactly one rank, e.g. 'straight to the jack'.",
        "house" : "A full house call requires exactly two ranks, e.g. 'full house, aces over 5s'.",
        "four" : "A four of a kind call requires exactly one rank, e.g. 'four 5s'.",
        "sflush" : "A straight flush call requires exactly one rank and suit, e.g. 'straight flush to the jack of hearts'." }

    def __init__(self, call):
        self.call = call

    def __str__(self):
        return "I couldn't parse your call. " + messages[call]


suits = ["C", "D", "H", "S"]

cards = []
for rank in xrange(2,15):
    for suit in suits:
        cards += [Card(rank=rank, suit=suit)]

ranked_hands = []
for rank in xrange(2,15): #High cards
    ranked_hands += [Hand([Card(rank=rank)])]

for rank in xrange(2,15): #Pairs
    ranked_hands += [Hand([Card(rank=rank), Card(rank=rank)])]
                     
for rank in xrange(2,15): #Two pairs
    for rank2 in xrange(rank+1, 15):
        ranked_hands += [Hand([Card(rank=rank), Card(rank=rank), Card(rank=rank2), Card(rank=rank2)])]

for rank in xrange(2,15): #Trips
    ranked_hands += [Hand([Card(rank=rank), Card(rank=rank), Card(rank=rank)])]

for suit in suits: #Flushes
    ranked_hands += [Hand([Card(suit=suit) for x in xrange(4)])]

for rank in xrange(2,11): #Straights
    ranked_hands += [Hand([Card(rank=x) for x in xrange(rank, rank+5)])]
for rank in xrange(2, 15): #Full houses
    for rank2 in xrange(2, 15):
        if rank == rank2:
            continue
        ranked_hands += [Hand([Card(rank=rank) for x in xrange(3)] + [Card(rank=rank2) for x in xrange(2)])]
for rank in xrange(2, 15): #Four of a kinds
    ranked_hands += [Hand([Card(rank=rank) for x in xrange(4)])]

for rank in xrange(2, 11): #Straight flushes
    for suit in suits:
        ranked_hands += [Hand([Card(rank=x, suit=suit) for x in xrange(rank, rank+5)])]

hand_args = {"highhand" : 0, "challenge" : 0, "high" : 1, "pair" : 1, "2pair" : 2, "three" : 1, "flush" : 1, "straight" : 1, "house" : 2, "four" : 1, "sflush" : 2}

def parse_move(move):
    parts = move.split(" ")

    if parts[0] not in hand_args.keys():
        raise BadCallException("parse")

    if parts[0] == "flush":
        return (parts[0], parts[1])
    if parts[0] == "sflush":
        return (parts[0], [int(parts[1]), parts[2]])
    if parts[0] in ["highhand", "challenge"]:
        return parts[0]
    return (parts[0], map(int, parts[1:]))


def construct_hand(call, args):
    if len(args) != hand_args[call]:
        raise BadCallException(call)
    

    if call in ["high", "pair", "three", "four", "straight","2pair", "house","sflush"]:
        if args[0] not in xrange(2,15):
            raise BadCallException(call)
    if call in ["2pair", "house"]:
        if args[1] not in xrange(2,15):
            raise BadCallException(call)
    if call in ["flush, sflush"]:
        if args[-1] not in suits:
            raise BadCallException(call)

    
    if call == "high":
        return Hand([Card(rank=args[0])])

    if call == "pair":
        return Hand([Card(rank=args[0]) for x in xrange(2)])

    if call == "2pair":
        return Hand([Card(rank=args[0]) for x in xrange(2)] + [Card(rank=args[1]) for x in xrange(2)])

    if call == "three":
        return Hand([Card(rank=args[0]) for x in xrange(3)])

    if call == "flush":
        return Hand([Card(suit=args[0]) for x in xrange(5)])

    if call == "straight":
        return Hand([Card(rank=args[0]-x) for x in xrange(4,-1,-1)])

    if call == "house":
        return Hand([Card(rank=args[0]) for x in xrange(3)] + [Card(rank=args[1]) for x in xrange(2)])
    
    if call == "four":
        return Hand([Card(rank=args[0]) for x in xrange(4)])

    if call == "sflush":
        return Hand([Card(rank=args[0]-x, suit=args[1]) for x in xrange(4,-1,-1)])

#True if challenge successful, False if called hand exists
def evaluate_challenge(call, game):
   
    twos_needed = len(call.cards)
    pool_cards = reduce(lambda x y: x + y.cards, game.hands, [])
   
    for card in call.cards:
        for i in xrange(len(pool_cards)):
            pool_card = pool_cards[i]
            if card.suit != "G":
                if card.suit != pool_card.suit:
                    continue
            if card.rank != 0:
                if card.rank != pool_card.rank:
                    continue

            twos_needed -= 1
            del pool_cards[i]
            break

    twos_present = len(filter(lambda x: x.rank == 2, pool_cards))
    if twos_present >= twos_needed:
        return False
    return True

def compare_hands(one, two):

    if one == None:
        return 0 if two == None else -1
    elif two == None:
        return 1

    try:
        one_index = ranked_hands.index(one)
    except ValueError:
        print "problem was " + str(one)

    try:
        two_index = ranked_hands.index(two)
    except ValueError:
        print "problem was " + str(two)


    return cmp(one_index, two_index)

def gameloop_2():

    players = []
    all_players_in = False

    while !all_players_in:
        new_player = raw_input("Enter player name: ")
        if new_player == "done":
            all_players_in = True
        else:
            players.append(new_player)
            print new_player + " accepted."
            print "Current players: " + str(players)

    game = Game(players)

    print "Game of " + str(len(game.players)) + " started."
    print "Hands by player: "
    for index, player in enumerate(game.players):
        print player, str(game.hands[index])

    game_over = False
    round_num = 1
    best_yet = None
    prev_call = None

    while !game_over:
        print "Round " + str(round_num)
        for player in game.players:
            call_string = raw_input(print player + ", make a call: ")
            try:
                parsed_move = parse_move(call_string)
            except BadCallException:
                print "I couldn't understand that hand :(\nTry again!"
                continue #FIXME
            if parsed_move = "challenge":
                challenge_result = evaluate_challenge(prev_hand)
                if challenge_result:
                    loser = game.players[game.players.index(player) - 1 % len(game.players)]
                else:
                    loser = player
                    
            print call, args
            hand = construct_hand(call, args)
            print str(hand)
            if compare_hands(hand, best_yet) <= 0:
                print "Please enter a higher hand."
                continue
            best_yet = hand
            print
            
            
        
    
    

def gameloop():
    best_yet = None
    prev_call = None
    while True:
        call_string = raw_input("poot hand > ")
        try:
            parsed_move = parse_move(call_string)
        except BadCallException:
            print "I couldn't understand that hand :(\nTry again!"
            continue
        if parsed_move = "challenge":
            challenge_result = evaluate_challenge(prev_hand)
        print call, args
        hand = construct_hand(call, args)
        print str(hand)
        if compare_hands(hand, best_yet) <= 0:
            print "Please enter a higher hand."
            continue
        best_yet = hand
        print

gameloop()
exit()











friends = api.GetFriends()
f = open("since", "r")
lines = f.readlines()
since = lines[-1][:-1]
f.close()
statuses = []
for u in friends:
    statuses += api.GetUserTimeline(None, u.id, u.screen_name, since, include_rts=True)

statuses += api.GetUserTimeline(None, None, None, since, include_rts=True)

out = codecs.open(keys.outfile, encoding="utf-8",  mode="a")

statuses.sort(key=lambda x: x.id)

d=datetime.datetime.now()
out.write(str(d) + "<br>")
for s in statuses:
    text = re.sub(r"(\w+://[\w.\-/#]+)", lambda x: "<a href="+x.group(0)+">"+x.group(0)+"</a>", s.text)
    out.write("<a href=http://twitter.com/"+s.user.screen_name+"/status/"+str(s.id)+">"+ s.user.name + "</a> ("+s.user.screen_name+"): " + text + "<br>") 


f = open("since", "w")


f.write(str(statuses[-1].id)+"\n")
f.close()
    
