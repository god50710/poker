# /usr/bin/env python2

import os
from time import gmtime, strftime
import json


def dump_to_json_file(msg):
    global folder_path
    global json_path
    global sn

    if not "folder_path" in globals():
        pwd = os.getcwd()
        folder_path = pwd + "/pokerlog/" + strftime("%Y%m%d-%H%M%S", gmtime())
        sn = 0
    if msg["eventName"] == "__game_start":
        sn += 1
        json_path = folder_path + "/" + str(sn) + ".json"
    if "json_path" not in globals():
        # not start to record
        return

    # dump to json_path
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    with open(json_path, mode='a') as f:
        f.write(json.dumps(msg) + "\n")
    if msg["eventName"] == "__game_over":
        del globals()["json_path"]


def read_from_json_file(path):
    msgs = []
    with open(path) as f:
        lines = f.readlines()
        for line in lines:
            jstr = line[:-1]
            msgs.append(json.loads(jstr))
    return msgs


# return rounds (list) and error message
def build_rounds(msgs):
    myRoundCnt = 0
    rounds = []
    state = "ready_for_new_round"
    line = 0

    for msg in msgs:
        line += 1
        event_name = msg["eventName"]
        data = msg["data"]
        display_msg(msg)

        if state == "ready_for_new_round":
            if event_name == "__game_over":
                print "skip:" + state + ", line: " + str(line) + ", " + event_name
                break
            elif event_name == "__new_round":
                print "skip:" + state + ", line: " + str(line) + ", " + event_name

                # new round
                myRoundCnt += 1
                print "myRoundCnt: " + str(myRoundCnt)
                r = {"round": data["table"]["roundCount"], "actions": []}
                state = "preflop"
                print "state change: " + state
            else:
                print "skip:" + state + ", line: " + str(line) + ", " + event_name

        elif state == "preflop":
            if event_name == "__deal":
                # change state
                state = "flop"
                print "skip:" + state + ", line: " + str(line) + ", " + event_name
            elif event_name == "__start_reload":
                state = "round_end"
                print "skip:" + state + ", line: " + str(line) + ", " + event_name
            elif event_name == "__action" or event_name == "__bet":
                print "skip:" + state + ", line: " + str(line) + ", " + event_name
            elif event_name == "__show_action" and data["table"]["roundName"] == "Deal":
                action = data["action"]  # get playername, action and bet-amount
                action["pot"] = data["table"]["totalBet"]
                action["state"] = state
                r["actions"].append(action)
                print "want:" + state + ", line: " + str(line) + ", " + event_name
            else:
                return rounds, ("parsing error, " + state + ", line: " + str(line) + ", " + event_name)

        elif state == "flop":
            if event_name == "__action" or event_name == "__bet":
                print "skip:" + state + ", line: " + str(line) + ", " + event_name
            elif event_name == "__deal":
                # change state
                state = "turn"
                print "skip:" + state + ", line: " + str(line) + ", " + event_name
            elif event_name == "__start_reload":
                state = "round_end"
                print "skip:" + state + ", line: " + str(line) + ", " + event_name
            elif event_name == "__show_action" and data["table"]["roundName"] == "Flop":
                print "want:" + state + ", line: " + str(line) + ", " + event_name
                ############
            else:
                return rounds, ("parsing error, " + state + ", line: " + str(line) + ", " + event_name)

        elif state == "turn":
            if event_name == "__show_action" and data["table"]["roundName"] == "Turn":
                print "want:" + state + ", line: " + str(line) + ", " + event_name
                ############
            elif event_name == "__action" or event_name == "__bet":
                print "skip:" + state + ", line: " + str(line) + ", " + event_name
            elif event_name == "__deal":
                # change state
                state = "river"
                print "skip:" + state + ", line: " + str(line) + ", " + event_name
            elif event_name == "__start_reload":
                state = "round_end"
                print "skip:" + state + ", line: " + str(line) + ", " + event_name
            else:
                return rounds, ("parsing error, " + state + ", line: " + str(line) + ", " + event_name)

        elif state == "river":
            if event_name == "__action" or event_name == "__bet":
                print "skip:" + state + ", line: " + str(line) + ", " + event_name
            elif event_name == "__start_reload":
                # change state
                state = "round_end"
                print "skip:" + state + ", line: " + str(line) + ", " + event_name
            elif event_name == "__round_end":
                ############## pad card info for each action
                print "skip:" + state + ", line: " + str(line) + ", " + event_name
                rounds.append(r)
                state = "ready_for_new_round"
            elif event_name == "__show_action" and data["table"]["roundName"] == "River":
                print "want:" + state + ", line: " + str(line) + ", " + event_name
                ############
            else:
                return rounds, ("parsing error, " + state + ", line: " + str(line) + ", " + event_name)

        elif state == "round_end":
            ############## pad card info for each action
            print "skip:" + state + ", line: " + str(line) + ", " + event_name
            rounds.append(r)
            state = "ready_for_new_round"
        else:
            return rounds, ("parsing error, " + state + ", line: " + str(line) + ", " + event_name)

    return rounds, "success at line: " + str(line) + ", " + "total lines: " + str(len(msgs)) + "."


def display_msg(msg):
    global s
    from visualize import snapshot
    if "s" not in globals():
        s = snapshot()
        print "new snapshot"
    s.display1(msg["eventName"], msg["data"])


if __name__ == '__main__':
    #  msg = {"abc": "def"}
    #  dump_to_json_file( msg )
    import visualize

    # msgs = read_from_json_file("/Users/pei/ai_contest/poker/jsondir/pokerlog.20180710-120915")
    msgs = read_from_json_file("/Users/pei/ai_contest/poker/pokerlog/20180711-071017/1.json")

    ### test visualize
    for msg in msgs:
        display_msg(msg)

    ### test build_rounds
    rounds, err = build_rounds(msgs)
    print err
