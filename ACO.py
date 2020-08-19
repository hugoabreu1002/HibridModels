import numpy as np
from tqdm import tqdm
from scipy.stats import mode

class ACO(object):
    """
        antNumber : number of ants
        
        alpha : parameter for probabilities matrix
        
        beta : parameter for probabilities matrix
        
        rho : for pherormone
        
        Q : for pherormone
        
        dimentionsRanges : must be a list of itretables
    
        fitenessFunction : must be like, and returns a float from 0 to inf, the smaller means the better
            result = fitenessFunction(self.Space(self.antsVertice[k_ant]), *fitnessFunctionArgs)
            
        fitnessFunctionArgs : args Diferent than the antsVertice in Space.    
    """

    fitnessFunctionArgs = None

    def __init__(self, antNumber, antTours, alpha, beta, rho, Q, dimentionsRanges, fitnessFunction, fitnessFunctionArgs=[]):
        self._alpha = alpha
        self._beta = beta
        self._dimentionsRanges = dimentionsRanges
        self._rho = rho
        self._Q = Q
        self._antNumber = antNumber
        self._antTours = antTours
        self._Dij = None
        self._Pij = None
        self._Tij = None
        self._Space = None
        self._antsVertice = None
        self._oldAntsVertice = None
        self.fitnessFunction = fitnessFunction
        self._fitnessFunctionArgs = fitnessFunctionArgs
        self._allBest = None
        self._allBestFitness = np.inf
        self._ants_History = None
    
    
    def setSpace(self):
        """
        Dimentions_Ranges: is a list of ranges. E.g:
            p = d = q = range(0, 2)
            Dimentions_Ranges = [p, d, q]
            
        The vertices of the graph will be a line of Space
        """
                
        rows = 1
        for d in self._dimentionsRanges:
            rows = len(d)*rows

        print("dimentions Ranges passed: ", self._dimentionsRanges)
        print("number of Space rows: ", rows)
        
        Space = np.zeros((rows, len(self._dimentionsRanges)))

        for r in range(rows):
            for di, dobjtec in enumerate(self._dimentionsRanges):
                if (r >= len(dobjtec)):
                    Space[r, di] = dobjtec[r%len(dobjtec)]
                else:
                    Space[r, di] = dobjtec[r]

        return Space    
    
    
    def initializeMatricesAndAntsPosition(self):    
        self._Space = self.setSpace()
        self._Dij = 1/np.zeros((self._Space.shape[0], self._Space.shape[0])) #np.ones((self._Space.shape[0], self._Space.shape[0]))#
        self._Pif = np.ones((self._Space.shape[0], self._Space.shape[0]))
        self._Tij = np.ones((self._Space.shape[0], self._Space.shape[0]))
        
        self._antsVertice = np.random.choice(range(self._Space.shape[0]), size=self._antNumber)
        self._oldAntsVertice = np.zeros(self._antNumber, dtype=int)
        self._ants_History = [None]*self._antTours
    
    def updateDij(self, Dij):
        """
        Dij and Pij will be only the matrix for the current possibilities
        Tij will be the pherormonen matrix for the whole graph
        
        fitnessFunction - lesser the better, so a good path should, Cj lesser than Ci
        Dij_ij = Exp((Cj-Ci)/Ci) + max 10% random
        Dij_ji = Exp((Ci-Cj)/Cj) + max 10% random
        
        the random idea is like the ants cant get the distance perfectly
        """
        
        for k_ant in range(self._antNumber):
            i = self._antsVertice[k_ant]
            for foo in range(self._antNumber):
                j = np.random.choice(range(self._Space.shape[0]))
                if Dij[i, j] == np.inf: #np.inf
                    Ci = self.fitnessFunction(self._Space[self._antsVertice[k_ant], :], self._fitnessFunctionArgs)
                    Cj = self.fitnessFunction(self._Space[j, :], self._fitnessFunctionArgs)
                    
                    Dij_ij = np.exp((Cj-Ci)/Ci)
                    Dij[i,j] = Dij_ij + Dij_ij*np.random.rand(1)/10
        
                    Dij_ji = np.exp((Ci-Cj)/Cj)
                    Dij[j,i] = Dij_ji + Dij_ji*np.random.rand(1)/10
        
        return Dij
    
                                          
    def updateTij(self, Tij, Dij, Ants, last_Ants, rho=0.5, Q=1):
        Dij_inf = Dij == np.inf
        Dij_notinf = Dij != np.inf
        Dij[Dij_inf] = Dij_notinf.max()

        sumdeltaTij = np.zeros(Tij.shape)

        for kij in zip(last_Ants, Ants):
            sumdeltaTij[kij] += Q/Dij[kij]

        Tij = (1-rho)*Tij + sumdeltaTij

        Tij += np.random.randint(1, size=Tij.shape)/10

        return Tij

                                          
    def updatePij(self, Pij, Tij, Dij, alpha=1, beta=1):
        Dij_inf = Dij == np.inf
        Dij_notinf = Dij != np.inf
        Dij[Dij_inf] = Dij_notinf.max()

        Pij = (Tij**alpha)/(Dij**beta)
        Pij += np.random.randint(1, size=Pij.shape)/10
        
        row_sums = Pij.sum(axis=1)
        Pij = Pij / row_sums[:, np.newaxis]
        
        return Pij


    def getHistorySolutions(self):
        #TODO
        return 0
    
    def plotHistorySolutions(self):
        #TODO
        return 0

    def updateAntsPosition(self, Ants, Pij, verbose=False):
        last_Ants = Ants.copy()

        for i in range(Ants.shape[0]):
            k = Ants[i]

            possible_move = np.argwhere(Pij[k,:] > 0).flatten()

            if possible_move.shape[0] != 0:
                weights = Pij[k, possible_move]/Pij[k, possible_move].sum()
                Ants[i] = np.random.choice(possible_move, p=weights)
            else:
                Ants[i] = np.random.choice(np.array(range(Pij.shape[1])))

            if verbose:
                print("Ant {} possibilities:".format(i))
                print(possible_move)
                print("Ant {} move from {} to {}".format(i, k, Ants[i]))

        return Ants, last_Ants
    
                                          
    def search(self, verbose=False):
        
        self.initializeMatricesAndAntsPosition()
        self._antsVertice = np.zeros(self._antNumber, dtype=int)
        self._oldAntsVertice = np.zeros(self._antNumber, dtype=int)
        
        for it in tqdm(range(self._antTours)):
            self._Dij = self.updateDij(self._Dij)
            if verbose:
                print("Dij: ")
                print(self._Dij)

            self._Tij = self.updateTij(self._Tij, self._Dij, self._antsVertice, self._oldAntsVertice, self._rho, self._Q)
            if verbose:
                print("Tij: ")
                print(self._Tij)

            self._Pij = self.updatePij(self._Pij, self._Tij, self._Dij)
            if verbose:
                print("Pij:")
                print(self._Pij)
            
            self._antsVertice, self._oldAntsVertice = self.updateAntsPosition(self._antsVertice.copy(), self._Pij, verbose)
            print(self._antsVertice)
            self._ants_History[it] = self._antsVertice.copy()
            
            tour_best = self._Space[mode(self._antsVertice)[0][0],:]
            tour_best_fitness = self.fitnessFunction(tour_best, self._fitnessFunctionArgs)
            if tour_best_fitness < self._allBestFitness:
                self._allBestFitness = tour_best_fitness
                self._allBest = tour_best

            if verbose:
                print("Dij: ")
                print(self._Dij)
                print("Tij: ")
                print(self._Tij)
                print("Pij:")
                print(self._Pij)
                print("Ants now - then")
                print(self._antsVertice, "-", self._oldAntsVertice)

        print("Most Frequent Last Tour Response")
        print(tour_best)
        print("Most Frequent Last Tour Fitness")
        print(tour_best_fitness)

        print("All Best Response")
        print(self._allBest)
        print("All Best Response Fitness")
        print(self._allBestFitness)

        self._ants_History = list(filter(lambda x: not x is None, self._ants_History))