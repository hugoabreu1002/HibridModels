from sklearn.metrics import mean_absolute_error as mae
from sklearn.model_selection import train_test_split
from sklearn.ensemble import VotingRegressor
from sklearn.datasets import make_regression
from sklearn import preprocessing
from hibridmodels.AgMlp import AgMlp as Ag_mlp
from hibridmodels.AGMLP_Residual import AGMLP_Residual
import numpy as np
import random
from tqdm import tqdm

class AGMLP_VR_Residual(AGMLP_Residual):

    def set_fitness(self, population, start_set_fit): 
        print('start_set_fit:', start_set_fit)
        
        for i in range(start_set_fit, len(population)):
            #erro estimado
            erro_train_entrada, erro_train_saida, erro_test_entrada, erro_test_saida = self.train_test_split(
                self._erro, population[i][0])
            
            #AG_erro
            print(population)
            percent_VR_heuristic = sum(population[i][0:5])/2 # population[i][0:5] são parâmetros da população, sendo cada um número entre 0 e 20 na média.
            if percent_VR_heuristic > 50:
                percent_VR_heuristic = 50
            
            VR_mlps_erro = Ag_mlp(erro_train_entrada, erro_train_saida, erro_test_entrada, erro_test_saida, self._num_epochs,
                                    self._size_pop, self._prob_mut).return_VotingRegressor(percent_VR_heuristic)

            erro_estimado = np.concatenate([VR_mlps_erro.VR_predict(erro_train_entrada), VR_mlps_erro.VR_predict(erro_test_entrada)])

            #y estimado
            X_ass_1_train_in, _, X_ass_1_test_in, _ = self.train_test_split(self._y_sarimax, population[i][1])
            X_ass_2_train_in, _, X_ass_2_test_in, _ = self.train_test_split_prev(erro_estimado, population[i][2],
                                                                                 population[i][3])

            X_in_train = np.concatenate((X_ass_1_train_in, X_ass_2_train_in), axis=1)
            X_in_test = np.concatenate((X_ass_1_test_in, X_ass_2_test_in), axis=1) 
            
            #AG_ASS
            VR_mlps_ass = Ag_mlp(X_in_train, self._data_train, X_in_test, self._data_test, self._num_epochs,
                                     self._size_pop, self._prob_mut).return_VotingRegressor(percent_VR_heuristic)
            
            
            population[i][4] = VR_mlps_erro
            population[i][5] = VR_mlps_ass
            population[i][-1] = mae(VR_mlps_ass.VR_predict(X_in_test), self._data_test)

        return population
