#! /usr/bin/env python
# -*- coding:utf-8 -*-

import json
import sys

class bcolors:
    PURLPLE = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.PURLPLE = ''
        self.BLUE = ''
        self.GREEN = ''
        self.YELLOW = ''
        self.RED = ''
        self.ENDC = ''

class snapshot:
  def __get_cards_str(self, cards):
    s = ""
    for c in cards:
      if len(s) == 0:
        s = "[" + c
      else:
        s = s + "," + str(c)
    if len(s)>0:
      s = s + "]"
    return s

  def __display_dic(self, dic, color, showkey, keycolor=True):
    memo=""
    key_str=""
    val_str=""
    # trans int/list/bool to str
    for key in dic:
      if (type(dic[key])) == int:
        dic[key]="%5d" % (dic[key])
      elif (type(dic[key])) == list:
        dic[key]=self.__list2str(dic[key])
      elif (type(dic[key])) == bool:
        if (dic[key]):
          dic[key]="Y"
        else:
          dic[key]=""

    # pick out memo
    if "memo" in dic:
      memo = dic["memo"]
      del(dic["memo"])

    # write key_str and val_str
    for key in dic:
      l_key = len(key)
      l_val = len(str(dic[key]))
      n = max(l_key, l_val) + 2
      for i in range(1,n-l_key):
        key_str = key_str + " "
      key_str = key_str + key
      for i in range(1,n-l_val):
        val_str = val_str + " "
      if key == "cards":
        c = bcolors.RED
      else:
        c = color
      val_str = val_str + c + str(dic[key]) + bcolors.ENDC
    
    # handle memo
    if (len(memo)):
      key_str = key_str + "  memo"
      val_str = val_str + "  " + color + memo + bcolors.ENDC
    
    #print
    if (showkey):
      if (keycolor):
        print color + key_str + "\n" + val_str
      else:
        print key_str + "\n" + val_str
    else:
        print val_str

  def __list2str(self, l):
    l_str = ""
    for i in l:
      if len(l_str) == 0 :
        l_str = str(i)
      else:
        l_str = l_str + " " + str(i)
    return l_str
    

  def display1(self, event_name, data):
    if event_name == "__new_round" or event_name == "__deal" or event_name == "_join":
      players = data["players"]
      table = data["table"].copy()
    elif event_name == "__round_end":
      players = data["players"]
      table = data["table"].copy()
    elif event_name == "__game_over":
      players = data["players"]
      table = data["table"].copy()
      winners = data["winners"]
    elif event_name == "__action" or event_name == "__bet":
      selff = data["self"].copy()
      table = data["game"].copy()
      players = table["players"]
      del(table["players"])
      table["tableNumber"]=data["tableNumber"]
    elif event_name == "__show_action":
      players = data ["players"]
      action = data["action"]
      table = data["table"].copy()
    elif event_name == "__start_reload":
      players = data ["players"]
    else: # event_name == "__game_prepare" or event_name =="__new_peer"
      print bcolors.YELLOW + event_name + bcolors.ENDC
      print json.dumps(data)
      return

    # print
    print bcolors.YELLOW + event_name + bcolors.ENDC
    # for table
    if "table" in locals():
      BB=table["bigBlind"]
      SB=table["smallBlind"]
      board=table["board"]
      del(table["bigBlind"])
      del(table["smallBlind"])
      del(table["board"])

      if event_name == "__deal":
        c = bcolors.YELLOW
      else:
        c = bcolors.GREEN
      print c + " board: " + bcolors.RED + self.__list2str(board) + bcolors.ENDC
      self.__display_dic(table, c, True)

    # for player
    showkey=True
    for p1 in players:
      p = p1.copy()
      p_action=""
      p_color=""
      # isSurvive, isOnline
      if 'action' in locals() and p["playerName"] == action["playerName"]:
        p_color = bcolors.YELLOW
#        p_action = action["action"] + (" " + str(action["amount"]) if ('amount' in action))
        p_action = action["action"]
        if ('amount' in action):
           p_action = p_action + " " + str(action["amount"])
      elif 'selff' in locals() and p["playerName"] == selff["playerName"]:
        p_color = bcolors.YELLOW
        p_action = "minBet " + str(selff["minBet"])
        del(p["minBet"])
      elif not p["isSurvive"] or ("isOnline" in p and not p["isOnline"]) or p["folded"]:
        p_color = bcolors.BLUE

      p["memo"]=[]
      # BB, SB, Action
      if "BB" in locals() and BB["playerName"] == p["playerName"]:
        p["memo"].append("[BB " + str(BB["amount"]) + "]")
      if "SB" in locals() and SB["playerName"] == p["playerName"]:
        p["memo"].append("[SB " + str(SB["amount"]) + "]")
      if len(p_action):
        p["memo"].append("[" + p_action + "]")

      # isHuman, folded
      if "isHuman" in p and p["isHuman"]:
        p["memo"].append("[H]")
      if p["folded"]:
        p["memo"].append("[F]")
      if "isHuman" in p:
        del(p["isHuman"])
      del(p["folded"])

      # cards
      if "cards" not in p:
        p["cards"]=[]

      # hand
      if "hand" in p:
        p["memo"].append("[" + str(p["hand"]["rank"]) + "]")
        p["memo"].append("[" + p["hand"]["message"] + "]")
        del(p["hand"])
      elif "winners" in locals():
        for p2 in winners:
          if (p["playerName"] == p2["playerName"]):
            p_color = bcolors.YELLOW
            p["memo"].append("[" + str(p2["hand"]["rank"]) + "]")
            p["memo"].append("[" + p2["hand"]["message"] + "]")
            p["memo"].append("[W]")

      self.__display_dic(p, p_color, showkey, False) 
      showkey = False

      # end of p in players
