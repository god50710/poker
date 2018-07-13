# coding=UTF-8
from pokereval.card import Card
# from deuces import Card, Evaluator
from pokereval.hand_evaluator import HandEvaluator
from websocket import create_connection
import random
import json


def getCard(card):
    card_type = card[1]
    cardnume_code = card[0]
    card_num = 0
    card_num_type = 0
    if card_type == 'H':
        card_num_type = 1
    elif card_type == 'S':
        card_num_type = 2
    elif card_type == 'D':
        card_num_type = 3
    else:
        card_num_type = 4

    if cardnume_code == 'T':
        card_num = 10
    elif cardnume_code == 'J':
        card_num = 11
    elif cardnume_code == 'Q':
        card_num = 12
    elif cardnume_code == 'K':
        card_num = 13
    elif cardnume_code == 'A':
        card_num = 14
    else:
        card_num = int(cardnume_code)

    return Card(card_num, card_num_type)


class PokerBot(object):
    def declareAction(self, hole, board, round, my_Raise_Bet, my_Call_Bet, Table_Bet, number_players, raise_count,
                      bet_count, my_Chips, total_bet):
        err_msg = self.__build_err_msg("declare_action")
        raise NotImplementedError(err_msg)

    def game_over(self, isWin, winChips, data):
        err_msg = self.__build_err_msg("game_over")
        raise NotImplementedError(err_msg)


class PokerSocket(object):
    ws = ""
    board = []
    hole = []
    my_Raise_Bet = 0
    my_Call_Bet = 0
    number_players = 0
    my_Chips = 0
    Table_Bet = 0
    playerGameName = None
    raise_count = 0
    bet_count = 0
    total_bet = 0

    def __init__(self, playerName, connect_url, pokerbot):
        self.pokerbot = pokerbot
        self.playerName = playerName
        self.connect_url = connect_url

    def getAction(self, data):
        round = data['game']['roundName']
        players = data['game']['players']
        chips = data['self']['chips']
        hands = data['self']['cards']

        self.raise_count = data['game']['raiseCount']
        self.bet_count = data['game']['betCount']
        self.my_Chips = chips
        self.playerGameName = data['self']['playerName']

        self.number_players = len(players)
        self.my_Call_Bet = data['self']['minBet']
        self.my_Raise_Bet = int(data['self']['minBet']) * 2
        self.hole = []
        for card in (hands):
            self.hole.append(getCard(card))

        print 'my_Call_Bet:{}'.format(self.my_Call_Bet)
        print 'my_Raise_Bet:{}'.format(self.my_Raise_Bet)
        print 'board:{}'.format(self.board)
        print 'total_bet:{}'.format(self.Table_Bet)
        print 'hands:{}'.format(self.hole)

        if self.board == []:
            round = 'preflop'

        print "round:{}".format(round)
        action, amount = self.pokerbot.declareAction(self.hole, self.board, round, self.my_Raise_Bet, self.my_Call_Bet,
                                                     self.Table_Bet, self.number_players, self.raise_count,
                                                     self.bet_count, self.my_Chips, self.total_bet)
        self.total_bet += amount
        return action, amount

    def takeAction(self, action, data):
        # Get number of players and table info
        if action == "__show_action" or action == '__deal':
            table = data['table']
            players = data['players']
            boards = table['board']
            self.number_players = len(players)
            self.Table_Bet = table['totalBet']
            self.board = []
            for card in (boards):
                self.board.append(getCard(card))
            print 'number_players:{}'.format(self.number_players)
            print 'board:{}'.format(self.board)
            print 'total_bet:{}'.format(self.Table_Bet)
        elif action == "__bet":
            action, amount = self.getAction(data)
            print "action: {}".format(action)
            print "action amount: {}".format(amount)
            self.ws.send(json.dumps({
                "eventName": "__action",
                "data": {
                    "action": action,
                    "playerName": self.playerName,
                    "amount": amount
                }}))
        elif action == "__action":
            boards = data['game']['board']
            self.board = []
            for card in (boards):
                self.board.append(getCard(card))
            action, amount = self.getAction(data)
            print "action: {}".format(action)
            print "action amount: {}".format(amount)
            self.ws.send(json.dumps({
                "eventName": "__action",
                "data": {
                    "action": action,
                    "playerName": self.playerName,
                    "amount": amount
                }}))
        elif action == "__round_end":
            print "Game Over"
            self.total_bet = 0
            players = data['players']
            isWin = False
            winChips = 0
            for player in players:
                winMoney = player['winMoney']
                playerid = player['playerName']
                if (self.playerGameName == playerid):
                    if (winMoney == 0):
                        isWin = False
                    else:
                        isWin = True
                    winChips = winMoney
            print "winPlayer:{}".format(isWin)
            print "winChips:{}".format(winChips)
            self.pokerbot.game_over(isWin, winChips, data)

    def doListen(self):
        try:
            self.ws = create_connection(self.connect_url)
            self.ws.send(json.dumps({
                "eventName": "__join",
                "data": {
                    "playerName": self.playerName
                }
            }))
            while 1:
                result = self.ws.recv()
                msg = json.loads(result)
                event_name = msg["eventName"]
                data = msg["data"]
                print event_name
                print data
                self.takeAction(event_name, data)
        except Exception, e:
            print e.message
            self.doListen()


class PotOddsPokerBot(PokerBot):

    def __init__(self, preflop_threshold, flop_threshold):
        self.preflop_threshold = preflop_threshold
        self.flop_threshold = flop_threshold

    def game_over(self, isWin, winChips, data):
        print "Game Over"

    def getCardID(self, card):
        if card.rank == 14:
            rank = 1
        else:
            rank = card.rank
        suit = card.suit
        suit = suit - 1
        id = (suit * 13) + rank
        return id

    def genCardFromId(self, cardID):
        if int(cardID) > 13:
            suit = (int(cardID) - 1) / 13 + 1
            rank = int(cardID) % 13
            if rank == 1:
                rank = 14
            elif rank == 0:
                rank = 13
        else:
            suit = 1
            if int(cardID) == 1:
                rank = 14
            else:
                rank = int(cardID)
        # print "rank", rank, "suit", suit
        return Card(rank, suit)

    def _pick_unused_card(self, card_num, used_card):
        used = [self.getCardID(card) for card in used_card]
        # print "used", used
        unused = [card_id for card_id in range(1, 53) if card_id not in used]
        # print "unused", unused
        choiced = random.sample(unused, card_num)
        # print "choiced", choiced
        return [self.genCardFromId(card_id) for card_id in choiced]

    def get_win_prob(self, hand_cards, board_cards, simulation_number, num_players):
        win = 0
        round = 0
        evaluator = HandEvaluator()
        for i in range(simulation_number):

            board_cards_to_draw = 5 - len(board_cards)  # 2
            board_sample = board_cards + self._pick_unused_card(board_cards_to_draw, board_cards + hand_cards)
            unused_cards = self._pick_unused_card((num_players - 1) * 2, hand_cards + board_sample)
            opponents_hole = [unused_cards[2 * i:2 * i + 2] for i in range(num_players - 1)]
            opponents_score = [pow(evaluator.evaluate_hand(hole, board_sample), num_players) for hole in
                               opponents_hole]
            my_rank = pow(evaluator.evaluate_hand(hand_cards, board_sample), num_players)
            if my_rank >= max(opponents_score):
                win += 1
            round += 1
        # The large rank value means strong hand card
        print "Win:{}".format(win)
        win_prob = win / float(round)
        print "win_prob:{}".format(win_prob)
        return win_prob

    def declareAction(self, hole, board, round, my_Raise_Bet, my_Call_Bet, Table_Bet, number_players, raise_count,
                      bet_count, my_Chips, total_bet):

        print "my_Chips", my_Chips, "my_Call_Bet", my_Call_Bet, "my_Raise_Bet", my_Raise_Bet, "Table_Bet", Table_Bet
        print "Round:{}".format(round)
        score = HandEvaluator.evaluate_hand(hole, board)
        print "hole", hole, "board", board
        print "score:{}".format(score)
        allin_static_rate = 0.94
        raise_static_rate = 0.9
        call_static_rate = 0.8
        in_montecarlo_rate = 0.69
        in_montecarlo_card = 4

        if my_Call_Bet == 0:
            action = 'call'
            amount = my_Call_Bet
        elif round == 'preflop' or round == 'Deal':
            if my_Call_Bet > my_Chips:
                my_Call_Bet = my_Chips
            ChipOdds = allin_static_rate * ((my_Call_Bet + total_bet) / float(my_Chips + total_bet)) ** 0.5
            if score >= ChipOdds * 3 and score >= raise_static_rate:
                action = 'raise'
                amount = my_Raise_Bet
            elif score >= ChipOdds * 2 and score >= self.preflop_threshold or score >= call_static_rate:
                action = 'call'
                amount = my_Call_Bet
            else:
                action = 'fold'
                amount = 0
            print "chipodds %s=((%s+%s) /(%s+%s))**0.5, call=%s, raise=%s" % (
                ChipOdds, my_Call_Bet, total_bet, my_Chips, total_bet, ChipOdds * 2, ChipOdds * 3)
        else:
            if my_Call_Bet > my_Chips:
                my_Call_Bet = my_Chips
            ChipOdds = allin_static_rate * ((my_Call_Bet + total_bet) / float(my_Chips + total_bet)) ** 0.5
            if score >= allin_static_rate and len(board)>=in_montecarlo_card:
                action = 'allin'
                amount = 0
            elif score >= allin_static_rate:
                action = 'bet'
                bet = ((my_Chips + total_bet)/3)-total_bet
                if bet > total_bet:
                    bet = my_Call_Bet
                amount = bet
            elif score >= ChipOdds * 3 and score >= self.flop_threshold or score >= raise_static_rate:
                action = 'raise'
                amount = my_Raise_Bet
            elif score >= ChipOdds * 2 and score >= self.flop_threshold or score >= call_static_rate:
                action = 'call'
                amount = my_Call_Bet
            else:
                action = 'fold'
                amount = 0
            print "chipodds %s=((%s+%s) /(%s+%s))**0.5, call>=%s, raise>=%s" % (
                ChipOdds, my_Call_Bet, total_bet, my_Chips, total_bet, ChipOdds * 2, ChipOdds * 3)
        if (action == 'call' or action == 'raise') and len(board) >= in_montecarlo_card and score <= in_montecarlo_rate:
            simulation_number = 50
            win_rate = self.get_win_prob(hole, board, simulation_number, number_players)
            if win_rate < 0.25:
                action = 'fold'
                amount = 0
            elif win_rate < 0.30:
                action = 'call'
                amount = my_Call_Bet
            elif win_rate < 0.35:
                action = 'raise'
                amount = my_Raise_Bet
            else:
                action = 'allin'
                amount = 0
            print 'change'
        return action, amount


if __name__ == '__main__':
    aggresive_threshold = 0.54
    passive_threshold = 0.7
    preflop_threshold_Loose = 0.2
    preflop_threshold_Tight = 0.4

    playerName = "KIHo"
    # connect_url = "ws://poker-dev.wrs.club:3001/"
    connect_url = "ws://poker-training.vtr.trendnet.org:3001/"
    myPokerBot = PotOddsPokerBot(preflop_threshold_Loose, aggresive_threshold)
    myPokerSocket = PokerSocket(playerName, connect_url, myPokerBot)
    myPokerSocket.doListen()
