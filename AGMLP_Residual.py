from sklearn.metrics import mean_absolute_error as mae
from sklearn.model_selection import train_test_split
from sklearn.ensemble import VotingRegressor
from sklearn.datasets import make_regression
from sklearn import preprocessing
from mlopt.AgMlp import AgMlp as Ag_mlp
import numpy as np
import random
from tqdm import tqdm

class AGMLP_Residual:
    # TODO documentar
    def __init__(self, data, y_sarimax, num_epochs = 10, size_pop=10, prob_mut=0.8, tr_ts_percents=[80,20], alpha_stop=1e-4):
        """
            data - original data
            y_sarimax - forecasted data
            num_epochs - number of epochs
            size_pop - size of population
            prob_mut - probability of mutation
            tr_ts_percents - list of train and test percentages. E.G: [80,20]
            alpha_stop - early stop criteria.
        """
        self._data = data
        self._data_train = data[:int(tr_ts_percents[0]/100*len(data))]
        self._data_test = data[int(tr_ts_percents[0]/100*len(data)):]
        self._y_sarimax = y_sarimax
        self._erro = data-y_sarimax
        self._data_train_arima = y_sarimax[:int(tr_ts_percents[0]/100*len(y_sarimax))]
        self._data_test_arima = y_sarimax[int(tr_ts_percents[0]/100*len(y_sarimax)):]
        self._num_epochs = num_epochs
        self._size_pop = size_pop
        self._prob_mut = prob_mut
        self._tr_ts_percents = tr_ts_percents
        self._alpha_stop = alpha_stop
        self._fitness_array = np.array([])
        self._best_of_all = None
        
    def early_stop(self):
        array = self._fitness_array
        to_break=False
        if len(array) > 4:
            array_diff1_1 = array[1:] - array[:-1]
            array_diff2 = array_diff1_1[1:] - array_diff1_1[:-1]
            if (array_diff2[-4:].mean() > 0) and (abs(array_diff1_1[-4:].mean()) < self._alpha_stop):
                to_break = True

        return to_break
        
    def train_test_split(self, serie, num_lags, print_shapes = False):
        """
            Slipts a time series to train and test Data.
            X data are data num_lags behind y data.
        """
        len_serie = len(serie)
        X = np.zeros((len_serie, num_lags))
        y = np.zeros((len_serie,1))
        for i in np.arange(0, len_serie):
            if i-num_lags>0:
                X[i,:] = serie[i-num_lags:i]
                y[i] = serie[i]

        len_train = np.floor(len_serie*self._tr_ts_percents[0]/100).astype('int')
        len_test = np.ceil(len_serie*self._tr_ts_percents[1]/100).astype('int')

        X_train = X[0:len_train]
        y_train = y[0:len_train]
        X_test = X[len_train:len_train+len_test]
        y_test = y[len_train:len_train+len_test]

        return X_train, y_train, X_test, y_test

    def train_test_split_prev(self, serie, num_lags_pass, num_lags_fut, print_shapes = False):
        """
            Slipts a time series to train and test Data.
            X data are data num_lags_pass behind and num_lags_fut ahead y data.
        """
        len_serie = len(serie)
        X = np.zeros((len_serie, (num_lags_pass+num_lags_fut)))
        y = np.zeros((len_serie,1))
        for i in np.arange(0, len_serie):
            if (i-num_lags_pass > 0) and ((i+num_lags_fut) <= len_serie):
                X[i,:] = serie[i-num_lags_pass:i+num_lags_fut]
                y[i] = serie[i]
            elif (i-num_lags_pass > 0) and ((i+num_lags_fut) > len_serie):
                X[i,-num_lags_pass:] = serie[i-num_lags_pass:i]
                y[i] = serie[i]

        len_train = np.floor(len_serie*self._tr_ts_percents[0]/100).astype('int')
        len_test = np.ceil(len_serie*self._tr_ts_percents[1]/100).astype('int')

        X_train = X[0:len_train]
        y_train = serie[0:len_train]
        X_test = X[len_train:len_train+len_test]
        y_test = y[len_train:len_train+len_test]

        return X_train, y_train, X_test, y_test
    
    def gen_population(self):
        """
            Generates the population. 
            The population is a list of lists where every element in the inner list corresponds to:
            [lag_residue_regression, lag_original_sarimax_association, lag_estimated_residue, forecast_estimated_residue
            , 'object_resiue_regression', 'object_association', fitness]
            
            The lags and forecast variables are token from a uniform distribution from 1 to 20.
        """
        population = [[1,1,1,1,'objeto_erro','objeto_ass',np.inf]]*self._size_pop
        for i in range(0, self._size_pop):
            population[i] = [random.randint(1, 20), random.randint(1, 20),  random.randint(1, 20), random.randint(1, 20), 'objeto_erro', 'objeto_ass', 10]
        
        return population

    def set_fitness(self, population, start_set_fit): 
        for i in range(start_set_fit, len(population)):
            #obter o erro estimado
            erro_train_entrada, erro_train_saida, erro_test_entrada, erro_test_saida = self.train_test_split(
                self._erro, population[i][0])
            
            #AG_erro
            Ag_mlp_erro = Ag_mlp(erro_train_entrada, erro_train_saida, erro_test_entrada, erro_test_saida, self._num_epochs,
                self._size_pop, self._prob_mut).search_best_individual()
            best_erro = Ag_mlp_erro._best_of_all
            
            erro_estimado = np.concatenate([best_erro.predict(erro_train_entrada), best_erro.predict(erro_test_entrada)])

            #obter o y estimado
            X_ass_1_train_in, _, X_ass_1_test_in, _ = self.train_test_split(self._y_sarimax, population[i][1])
            X_ass_2_train_in, _, X_ass_2_test_in, _ = self.train_test_split_prev(erro_estimado, population[i][2],
                                                                                 population[i][3])

            X_in_train = np.concatenate((X_ass_1_train_in, X_ass_2_train_in), axis=1)
            X_in_test = np.concatenate((X_ass_1_test_in, X_ass_2_test_in), axis=1) 
            
            #AG_ASS
            Ag_MLP_ass = Ag_mlp(X_in_train, self._data_train, X_in_test, self._data_test, self._num_epochs,
                                     self._size_pop, self._prob_mut).search_best_individual()
            best_ass = Ag_MLP_ass._best_of_all   
            
            
            population[i][-3] = best_erro
            population[i][-2] = best_ass
            population[i][-1] = mae(best_ass.predict(X_in_test), self._data_test)

        return population
    
    def cruzamento(self, population):
        """
            Crossover 
            the next population will receive the first 2 cromossoma
        """
        len_cross = len(population[0][:-3]) #gets the length of cromossomos, cutting the last three objetcts wich doest count as cromossoma.
        pop_ori = population
        len_pop = len(pop_ori)
        # do a loop for every individual keeping the first individual always.
        for p in range(1, len_pop):
            # if the proabiblity matches
            if np.random.rand() > (1 - self._prob_mut):
                # first half of cromossoma are taken from the simetric individual on the left (better)
                qt_to_cross = np.random.randint(0,len_cross)
                cromossoma_to_cross = np.random.choice(list(range(0,len_cross)), qt_to_cross)
                individual_to_take = int(p/2)
                for ctc in cromossoma_to_cross:
                    population[p][ctc] = pop_ori[individual_to_take][ctc]

        return population

    def mutation(self, population):
        for p in range(1, len(population)):
            if np.random.rand() > (1 - self._prob_mut):
                population[p][0] = population[p][0] + np.random.randint(-2, 2)
                if population[p][0] <= 0:
                    population[p][0] = 1
                
                population[p][1] = population[p][1] + np.random.randint(-2, 2)
                if population[p][1] <= 0:
                    population[p][1] = 1
                
                population[p][2] = population[p][2] + np.random.randint(-2, 2)
                if population[p][2] <= 0:
                    population[p][2] = 1
                
                population[p][3] = population[p][3] + np.random.randint(-2, 2)
                if population[p][3] <= 0:
                    population[p][3] = 1

        return population


    def new_gen(self, population, num_gen):
        """
            gets population already sorted, then do:
                crossover
                mutation
                set new fitness
                sort
        """
        population = self.cruzamento(population)
        population = self.mutation(population)
        population = self.set_fitness(population, int(self._size_pop*num_gen/(2*self._num_epochs)))
        population.sort(key = lambda x: x[:][-1]) 
        
        return population

    def search_best_model(self):
        ng = 0
        population = self.gen_population()
        population = self.set_fitness(population, ng)
        
        population.sort(key = lambda x: x[:][-1])
        self._fitness_array = np.append(self._fitness_array, population[0][-1])
        self._best_of_all = population[0]
        
        for ng in tqdm(range(0, self._num_epochs)):
            print('generation:', ng)
            population = self.new_gen(population, ng)
            if population[0][-1] < min(self._fitness_array):
                self._best_of_all = population[0]

            if self.early_stop():
                break
                
        return self