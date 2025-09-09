#this file is for the score input, both live and post-match
from random import randint

class Match:
    def __init__(self, final_score: int, match_type: str, deuce: bool, players: list):
        self.final_score = final_score
        self.match_type = match_type
        self.deuce = deuce
        self.players = players

        if match_type == "s":
            self.team1, self.team2 = self.players[0], self.players[1]
            #2 players in seperate teams for singles
        
        elif match_type == "d":
            self.team1 = [self.players[0], self.players[1]]
            self.team2 = [self.players[2], self.players[3]]
            #4 players in 2 seperate teams
            
        
class live_match(Match):
    def __init__(self, final_score: int, match_type: str, deuce: bool, players: list):
        super().__init__(final_score, match_type, deuce, players)
        self.court = [[],
                      []]
        
        self.court[0], self.court[1] = self.team1, self.team2
        #place players on 2d array of court
        self.score = [0, 0]
        self.match_start = False
        self.previous_point_winner = 0
        #empty as no point taken place

    def service(self, point_winner: int):
    #calculates which side and player serves next
        if self.match_start == False:
            service_side = randint(0,1)
            #chooses a random side to serve first
            self.previous_point_winner = service_side
            #so if same team scores again, same person will serve again on opposite side
            self.match_start = True

            if self.match_type == "s":
            #position of player serving in singles
                if service_side == 0:
                    return [self.team1, "right"]
                else:
                    return [self.team2, "right"]
            else:
                if service_side == 0:
                    return self.team1[1]
                else:
                    return self.team2[1]
        else:
            if self.match_type == "d":
                if self.score[point_winner] % 2 == 0:
                #if score is even
                    if point_winner == self.previous_point_winner:
                        #same team serves again
                        self.previous_point_winner = point_winner
                        self.court[point_winner][0], self.court[point_winner][1] = self.court[point_winner][1], self.court[point_winner][0]
                        return self.court[point_winner][1]
                    else:
                        #different team serves
                        self.previous_point_winner = point_winner
                        return self.court[point_winner][1]
                else:
                #if score is odd
                    if point_winner == self.previous_point_winner:
                        #same team serves again
                        self.previous_point_winner = point_winner
                        self.court[point_winner][0], self.court[point_winner][1] = self.court[point_winner][1], self.court[point_winner][0]
                        return self.court[point_winner][0]
                    else:
                        #different team serves
                        self.previous_point_winner = point_winner
                        return self.court[point_winner][0]
                
            else:
                self.previous_point_winner = point_winner
                if self.score[point_winner] % 2 == 0:
                    return [self.court[point_winner], "right"]
                else:
                    return [self.court[point_winner], "left"]

    def point(self, team):
    #adds point to team who scores.
        self.score[team] += 1
        if self.score[team] == self.final_score:
            if team == 0:
                other = 1
            else:
                other = 0

            if not self.deuce:
                print("match ended")
                #should stop and store the score in a database of some sort
            else:
                if self.score[team] == self.score[other] + 2:
                    print("match ended")
                    #should stop and store the score in a database of some sort

            



class finished_match(Match):
    def score(self, scores: list): 
        return {"team_1": scores[0], "team_2": scores[1]}
        #to add extra stuff to do with adding scores to a database where they can be processed to change player ranking


