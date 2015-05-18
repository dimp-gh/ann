# -*- coding: utf-8 -*-
from pybrain.datasets import SupervisedDataSet, ClassificationDataSet
from pybrain.tools.shortcuts import buildNetwork
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.structure.modules import SoftmaxLayer
from pybrain.utilities import percentError
from collections import OrderedDict

import dataset


class NN:
    def __init__(self):
        pass

    def load_dataset(self):
        csvs = [
            # 'peritonitis.csv',
            'appendicitis.csv',
            'hepatitis.csv',
            # 'ori.csv',
            # 'frk.csv',
        ]
        data = dataset.form_dataset(csvs)
        self.diagnoses = dataset.get_diagnoses(data)
        for d in self.diagnoses:
            print d,
        print
        self.data = dataset.normalize_dataset(data)

    def make_target(self, diagnosis):
        target = [0.0] * len(self.diagnoses)
        index = self.diagnoses.index(diagnosis)
        target[index] = 1.0
        return target

    def make_input(self, sample):
        input = []
        for field in dataset.fields:
            input.append(sample[field.name])
        return input

    def build_pybrain_dataset(self):
        field_count = len(dataset.fields)

        diagnoses_count = len(self.diagnoses)

        supervised_dataset = SupervisedDataSet(field_count, diagnoses_count)
        # supervised_dataset = ClassificationDataSet(field_count,
        #                                            diagnoses_count,
        #                                            nb_classes=diagnoses_count,
        #                                            class_labels=self.diagnoses)

        for sample in self.data:
            input = self.make_input(sample)
            diagnosis = sample['Диагноз']
            target = self.make_target(diagnosis)
            supervised_dataset.addSample(input, target)

        self.supervised_dataset = supervised_dataset
        # self.training_dataset = supervised_dataset
        # self.testing_dataset = supervised_dataset
        self.training_dataset, self.testing_dataset = supervised_dataset.splitWithProportion(0.7)

    def build_network(self):
        self.neural_network = buildNetwork(self.training_dataset.indim,
                                           22,
                                           self.training_dataset.outdim)
                                           #outclass=SoftmaxLayer)

    def build_trainer(self):
        self.trainer = BackpropTrainer(self.neural_network,
                                       self.training_dataset)

    def test_on_data(self, verbose=True):
        matched = 0.0
        diag_counter = OrderedDict((d, (0, 0)) for d in self.diagnoses)
        for input, target in self.testing_dataset:
            prediction = self.neural_network.activate(input)
            actual_diagnosis = self.diagnoses[target.argmax()]
            predicted_diagnosis = self.diagnoses[prediction.argmax()]
            if target.argmax() == prediction.argmax():
                matched += 1
                pos, neg = diag_counter[actual_diagnosis]
                diag_counter[actual_diagnosis] = (pos + 1, neg)
            else:
                pos, neg = diag_counter[actual_diagnosis]
                diag_counter[actual_diagnosis] = (pos, neg + 1)
        if verbose:
            for diag, (pos, neg) in diag_counter.items():
                print diag, ':', pos, neg
        return matched / len(self.testing_dataset)

    def train_classifier(self, epochs=50, verbose=True):
        for i in range(epochs):
            self.trainer.trainEpochs(1)
            trnresult = percentError(self.trainer.testOnClassData(),
                                     self.training_dataset['class'])
            tstresult = percentError(self.trainer.testOnClassData(dataset=self.testing_dataset),
                                     self.testing_dataset['class'])

            if verbose:
                print "epoch: %4d" % self.trainer.totalepochs, \
                    "  train error: %5.2f%%" % trnresult, \
                    "  test error: %5.2f%%" % tstresult

    def train_supervised(self, epochs=50):
        for i in range(epochs):
            self.trainer.trainEpochs(1)
            print 'SUCCESS:', self.test_on_data(verbose=True)

nn = NN()
nn.load_dataset()
nn.build_pybrain_dataset()
nn.build_network()
nn.build_trainer()
BEFORE = nn.test_on_data()
nn.train_supervised(epochs=1000)
AFTER = nn.test_on_data()
print 'BEFORE %s => AFTER %s' % (BEFORE, AFTER)
