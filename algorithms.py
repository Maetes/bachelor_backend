import time
import pandas as pd
from eclat.runner import main
from mlxtend.frequent_patterns import apriori, fpgrowth
from mlxtend.frequent_patterns import association_rules
from mlxtend.preprocessing import TransactionEncoder
from benchmark import Benchmark
import json
import os, csv
from flask import current_app as app

class Algorithms():
    def __init__(self, algorithm, data, support, confidence):
        self.algorithm = algorithm
        self.data = data
        self.support = support
        self.confidence = confidence

    def runFP(self, filename = 0):
        class returnObj():
            class start():
                pass
            class end():
                pass

        startBencher = Benchmark()
        startBencher.start()
        cpuStart, memoryStart = startBencher.stop()
        startBencher.join()
        returnObj.start.cpu = cpuStart
        returnObj.start.memory = memoryStart

        if(self.algorithm == "apriori" or self.algorithm == "fpgrowth"):
            transcoder = TransactionEncoder()
            data = []
            with open(self.data, 'r', encoding='utf-8') as f:
                i = csv.reader(f, delimiter=',', quotechar='\t')
                for row in i:
                    data.append(row)
            hardwareBencher = Benchmark()
            hardwareBencher.start()
            startTime = time.time()
            freq_items= apriori(pd.DataFrame(transcoder.fit(data).transform(data), columns=transcoder.columns_, dtype=bool),min_support=self.support,use_colnames=True) if self.algorithm == 'apriori' else fpgrowth(pd.DataFrame(transcoder.fit(data).transform(data), columns=transcoder.columns_, dtype=bool),min_support=self.support,use_colnames=True)
            endTime = time.time() - startTime
            cpuBench, memoryBench = hardwareBencher.stop()
            hardwareBencher.join()
            #freq_items["length"] = freq_items["itemsets"].apply(lambda x: len(x))

            returnObj.end.freq = freq_items
            returnObj.end.time = endTime
            returnObj.end.cpu = cpuBench
            returnObj.end.memory = memoryBench

            if(filename == 0):
                return returnObj
            else:
                if(returnObj.end.freq.empty):
                    self.dumpData('Keine FrequentItemsets gegunden!', filename)
                else:
                    mapped = self.mapFP(returnObj)
                    self.dumpData(mapped, filename)

        elif(self.algorithm == 'eclat'):
            returner = main('eclat', self.data, self.support)
            if(filename == 0):
                return returner
            else:
                if(returner.end.freq.empty):
                    self.dumpData('Keine FrequentItemsets gegunden!', filename)
                else:
                    mappedData = self.mapFP(returner)
                    self.dumpData(mappedData, filename)
        else:
            raise ValueError('Gewählter Algorithmus ungültig!')
    
    def mapFP(self, eval):
        returner = {
                    'config':{
                        'Algorithmus':self.algorithm,
                        'Datenset': self.data.split('/')[-1],
                        'Support': self.support,
                        'Konfidenz': self.confidence
                    },
                    'start': {
                        'freqItems': {
                            'cpu': eval.start.cpu,
                            'memory': eval.start.memory
                        }
                    },
                    'end':{
                        'freqItems': {
                            'freq': eval.end.freq.to_json(orient='records'),
                            'cpu': eval.end.cpu,
                            'memory': eval.end.memory,
                            'time': eval.end.time
                        }
                    }
                }
        return returner

    def dumpData(self, data,filenanme):
        with open(os.path.join('results', filenanme + '.json'), 'w') as f:
            json.dump(data, f, ensure_ascii=False)

    def runAR(self, freq_items):
        class returnObj():
            class start():
                pass
            class end():
                pass
        
        startBencherAsso = Benchmark()
        startBencherAsso.start()
        cpuStart, memoryStart = startBencherAsso.stop()
        startBencherAsso.join()
        returnObj.start.cpu = cpuStart
        returnObj.start.memory = memoryStart

        hardwareBencher = Benchmark()
        hardwareBencher.start()
        startTime = time.time()
        associations = association_rules(freq_items, metric="confidence", min_threshold=self.confidence)
        endTime = time.time() - startTime
        cpuBench, memoryBench = hardwareBencher.stop()
        hardwareBencher.join()

        returnObj.end.asso = associations
        returnObj.end.time = endTime
        returnObj.end.cpu = cpuBench
        returnObj.end.memory = memoryBench

        return returnObj
    
    def runFPandAR(self, id):
        freq = self.runFP()
        if(freq.end.freq.empty):
            returner = 'Keine FrequentItemsets gegunden!'
        else:
            asso = self.runAR(freq.end.freq)
            returner = {
                    'config':{
                        'Algorithmus':self.algorithm,
                        'Datenset': self.data.split('/')[-1],
                        'Support': self.support,
                        'Konfidenz': self.confidence
                    },
                    'start': {
                        'freqItems': {
                            'cpu': freq.start.cpu,
                            'memory': freq.start.memory
                        },
                        'association': {
                            'cpu': asso.start.cpu if asso else None,
                            'memory': asso.start.memory if asso else None
                        }
                    },
                    'end': {
                        'freqItems': {
                            'freq': freq.end.freq.to_json(orient='records') if freq.end.freq.empty != True else None,
                            'cpu': freq.end.cpu,
                            'memory': freq.end.memory,
                            'time': [freq.end.time]
                        },
                        'association': {
                            'asso': asso.end.asso.to_json(orient='records') if asso.end.asso.empty != True else None,
                            'cpu': asso.end.cpu if asso else None,
                            'memory': asso.end.memory if asso else None,
                            'time': [asso.end.time] if asso else None,
                        }
                    }
            }
        self.dumpData(returner, id)