"""
Spyder Editor

@author: vetter

"""

# Ein Corona-Ausbreitungsmodell

# Diese v2 dient zur Analyse der (Wieder)Ausbruchschancen des Virus, wenn schon
# teile immun sind. Daher wurde der Parameter zu Beginn bereits "immune Familien" 
# implementiert. Stellt man diesen Parameter auf Null, hat man wieder v1.



#%%

import numpy as np
import pandas as pd
import math
import os
import matplotlib.pyplot as plt

#%%
'''
VORUEBERLEGUNGEN:

Das Modell soll die Ausbreitung der Krankheit simulieren.

Entscheidend ist die Ausbreitungsrate (R). Exogen wird festgelegt, wie hoch sie ist.

Erster Schritt und einfachstes Modell: Die Ausbreitungsrate wird eingegeben: -> Modell ist nicht mehr als
eine Gleichung: 
    
    CovFaelle_neu = CovFaelle_alt * (R+1)
    
Wenn man Heilung einbezieht, erhält man:
    
    
    CovFaelle_neu = CovFaelle_alt * R
    
Wenn man von Wochen ausgeht und davon ausgeht, dass die Menschen zwar nur eine Woche ansteckend sind, die 
Krankheit aber zwei Wochen haben:
    
    
    CovFaelle_neu = CovFaelle_alt * R 
    
    CovFaelle_open = CovFaelle_neu + CovFaelle_alt = CovFaelle_alt * (R+1)
    


DIESES MODELL:
    
Drei Classen: 
    
    People: Bei Kontakt mit Mensch mit Virus wird man zu 50% (anfangs 100%) auch infiziert.
        -> enthält Info: krank ja/nein
        -> enthält Info: war schon mal krank (-> dann nicht mehr ansteckend)
        -> anfänglich reicht es, nur eine Woche krank und ansteckend zu sein
    
    Family: Peer mit 4 Personen, in der man sich stetig aufhält. Jede*r hat genau eine Familie.
        -> enthält Info, wer in Familie ist
        
    Main:
        -> enthält Liste mit den Familien.
        -> enthält Liste mit allen Bürger*innen
    
Annahme: Jeder hat eine "Familie" von vier Personen. Das muss nicht eine echte Familie sein, eine Peer ist 
genauso denkbar.
Zusätzlich sieht jeder pro Woche weitere Personen. Wenn einer in der Familie krank ist, sind sofort alle
krank. Wenn man einen Kranken trifft, wird man mit einer Wahrscheinlichkeit auch krank.

1 Periode = 1 Woche (entspricht etwa der ansteckenden Zeit, diese ist zwar eigentlich etwas länger, aber wer
Symptome hat, bleibt wahrscheinlich zuhause und steckt dann niemand mehr an)

Zufällige Begegungen: 
    - diese können anfangs aus dem ganzen Land sein
    - diese könnten auch regional beschränkt sein (nicht simuliert)
    - diese können anfangs unidirectional sein (wie simuliert)
    - später kann man sie als echte Begegnung simulieren (symmetrische Begegnungen, nicht simuliert)

    

'''

#%%

class People:
    def __init__(self, ill=0, immun=0):
        self.ill = ill # dieser Wert ist 0 oder 1, 1 für akut erkrankt
        #### self.time_ill = float ("nan")  # hier wird der Zeitpunkt der Erkrankung festgehalten
        self.immun = immun # ist 0 ider 1, 1 für bereits immun
    
            
    def infect(self):
        '''
        - man wird infiziert, falls man nicht immun ist
        - wenn man infiziert wird, wird man auch sofort immun (und nie wieder infiziert)
        '''
        if self.immun == 0:
            self.ill = 1
            self.immun = 1
            
    def recover(self):
        if self.ill == 1:
            self.ill = 0
    

class Family:
    
    def __init__(self, family):
        self.family = family
 
class Main:
    
    def __init__(self, n_families , n_families_immun,  n_families_ill , weeks , prob_social_dis):
        self.prob_social_dis = prob_social_dis
        self.weeks = weeks
        self.people = list()
        self.families = list()
        self.n_families = n_families
        self.n_families_ill = n_families_ill
        self.n_families_immun = n_families_immun
        self.n_ill = n_families_ill * 4
        self.n_immun = (n_families_immun + n_families_ill) * 4
        self.n_healthy = (n_families - n_families_ill) * 4
        self.n_all = n_families * 4
        self.q_ill = [self.n_ill / self.n_all]  # Quote Menschen mit Covid
        self.q_immun = [ self.n_immun / self.n_all ]  # Quote Menschen mit Covid
        
    def create_fam(self):
        fam_new = list()
        for i in range(4):
            xy = People()
            fam_new.append( xy )
            #self.people.append( xy )
        self.families.append( fam_new )
        
        
    def socializing(self, person_a):
        '''
        Diese Funktion ist zentral. Socializing wird immer gemacht, hier wird definiert in welchem Ausmass.
        Entscheidend sind:
            - Die Quote derer, die momentan krank und ansteckend sind -> q_ill
            - wie viele Leute man in der Woche sieht  -> bisher eine Person pro Woche
            - wie groß die Wahrscheinlichkeit der Ansteckung ist, wenn man sich sieht -> prob_social_dis
        '''
        infect = 0
        prob_person_b_ill = self.q_ill[-1]
        prob_social_dis = self.prob_social_dis 
        prob_social_infect = prob_social_dis * prob_person_b_ill
        if person_a.ill == 0 and person_a.immun == 0 and np.random.random() < prob_social_infect :
            person_a.infect()
            infect = 1
        return infect
        
        
    def initialization(self):
        '''
        - Kreiert die Familien inkl. der Menschen darin.
        - Macht eine bestimmte Anzahl an Famlien zu beginn krank.
        '''
        
        for i in range(self.n_families):
            self.create_fam()
            
        for i in range(self.n_families_ill):
            for j in range(4):
                self.families[i][j].infect()
        
        for i in range(self.n_families_ill, self.n_families_ill+self.n_families_immun):
            for j in range(4):
                self.families[i][j].immun = 1

    
    def timestep(self):
        
        # RECOVER
        for i in range(self.n_families):
            for j in range(4):
                if self.families[i][j].ill == 1:
                    self.families[i][j].ill = 0
                    self.n_ill += -1
                    self.n_healthy += 1
    
                
                
        # SOCIALIZING / GOING OUTSIDE
        for i in range(self.n_families): # Alle Leute aller Familien gehen einmal raus und begegnen einer Person, inkl. möglicher Infektion.
            infected = 0
            for j in range(4): # Leute innerhalb der Familien
                infected += self.socializing( self.families[i][j] )
            if infected > 0:   # falls sich jemand infiziert hat, sollen es alle bekommen
                for k in range(4):
                    self.families[i][k].infect()
                self.n_ill += 4
                self.n_immun += 4
                self.n_healthy += -4
                    
                    
    def run(self):
        self.initialization()
        for i in range(self.weeks):
            self.q_ill.append( self.n_ill / self.n_all )
            self.q_immun.append( self.n_immun / self.n_all )
            self.timestep()
        

    

#%%

COV = Main (n_families = 1000 , n_families_immun = 0 , n_families_ill = 1, weeks = 52 , prob_social_dis = 0.4)    
COV.run()            


#%%

fig, ax = plt.subplots(figsize = (8,4))
# Das ist eine nette Größe

ax.plot(range(COV.weeks+1), COV.q_ill)
#ax.plot(ts_frame["Weeks"], ts_frame["Quota COVID-19"])  # falls ich es in einem Data Frame speichert, brauche ich diese Zeile
ax.plot(range(COV.weeks+1), COV.q_immun)

# MODIFIKATIONEN (ZUR SCHÖNHEIT) 
# WICHTIG: Diese Schritte müssen direkt darauf folgen!

# LINEN OBEN UND RECHTS ENTFERNEN
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# ORIENTIERUNGSLINIEN
ax.yaxis.grid(color = "grey",
              linestyle = "--",
              linewidth = .5,
              alpha = 0.45)
# alpha ist zur Transparenz der Linien

# TITEL ZUM PLOT HINZUFÜGEN
ax.set_title("Spread of COVID-19")
ax.set_xlabel("Weeks")
ax.set_ylabel("Covid Cases")

# PLOT SPEICHERN
name = "output/COVID_"+str(COV.n_families)+"_"+str(COV.n_families_immun)+"_"+str(COV.n_families_ill)+"_"+str(COV.weeks)+"_"+str(COV.prob_social_dis)+"_4Personsfamily"+".pdf"
plt.savefig(str(name), bbox_inches= "tight")

#%%

#%%