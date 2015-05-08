# -*- coding: utf-8 -*-
import csv
import json
from collections import namedtuple, OrderedDict
from random import random, shuffle

import utils

DatasetField = namedtuple('DatasetField', 'name, pretty_name, valid_range')

text_fields = ['ФИО', 'Диагноз', 'Год', '№ карты']
fields = [
    DatasetField('WBC', 'Лейкоциты', (0.0, 50.0)),
    DatasetField('RBC', 'Эритроциты', (0.0, 10.0)),
    DatasetField('HGB', 'Гемоглобин', (10.0, 300.0)),
    DatasetField('HCT', 'Гематокрит', (0.0, 1.0)),
    DatasetField('MCV', 'Средний объём эритроцита', (0.0, 200.0)),
    DatasetField('MCH', 'Среднее содержание гемоглобина в эритроците', (1.0, 300.0)),
    DatasetField('MCHC', 'Средняя концентрация гемоглобина в эритроците', (100.0, 700.0)),
    DatasetField('PLT', 'Тромбоциты', (0.0, 800.0)),
    DatasetField('LYM%', 'Относительное содержание лимфоцитов', (0.0, 1.0)),
    DatasetField('MXD%', 'Относительное содержание смеси моноцитов, базофилов и эозинофилов', (0.0, 1.0)),
    DatasetField('NEUT%', 'Относительное содержание нейтрофилов', (0.0, 1.0)),
    DatasetField('LYM#', 'Абсолютное содержание лимфоцитов', (0.0, 50.0)),
    DatasetField('MXD#', 'Абсолютное содержание свеми моноцитов, базофилов и эозинофилов', (0.0, 5.0)),
    DatasetField('NEUT#', 'Абсолютное содержание нейтрофилов', (0.0, 100.0)),
    DatasetField('RDW-SD', 'Относительная ширина распределения эритроцитов по объёму', (30.0, 100.0)),
    DatasetField('RDW-CV', 'Относительная ширина распределения эритроцитов по объёму', (0.0, 1.0)),
    DatasetField('PDW', 'Относительная ширина распределения тромбоцитов по объёму', (5.0, 30.0)),
    DatasetField('MPV', 'Средний объем тромбоцитов', (1.0, 15.0)),
    DatasetField('P-LCR', 'Коэффициент больших тромбоцитов', (0.0, 1.0)),
]
field_map = OrderedDict((field.name, field) for field in fields)


def random_float(left, right):
    return left + (right - left) * random()


def make_average_value(field_name):
    field = field_map[field_name]
    min, max = field.valid_range
    center = (min + max) / 2.0
    delta = (max - min) / 100.0
    return random_float(center - delta, center + delta)


def parse_dirty_dataset(path):
    rows = []
    with open(path) as csvfile:
        for row in csv.DictReader(csvfile):
            record = {}
            for field_name, value in row.items():
                if field_name in field_map:
                    value = value.strip().replace(',', '.')
                    if utils.isfloat(value):
                        value = float(value)
                    elif value == '-' or value == '':
                        value = make_average_value(field_name)
                elif field_name in text_fields:
                    pass
                else:
                    raise Exception("unknown field '%s'" % repr(field_name))
                record[field_name] = value
            rows.append(record)
    return rows


def check_dataset(dataset):
    "check dataset for range errors"
    for row in dataset:
        for field_name, value in row.items():
            if field_name in field_map:
                field = field_map[field_name]
                min, max = field.valid_range
                if not (min <= value <= max):
                    raise Exception("Record '%s' doesn't fit into ranges in field '%s' (%s </= %s </= %s)" % (row['ФИО'], field_name, min, value, max))


def check_normalized_dataset(normalized_dataset):
    "check dataset for range errors"
    for row in normalized_dataset:
        for field_name, value in row.items():
            if field_name in field_map:
                if not (0 <= value <= 1):
                    raise Exception("Record '%s' doesn't fit into normalized ranges in field '%s' (0 </= %s </= 1)" % (row['ФИО'], field_name, value))
    return True


def get_diagnoses(dataset):
    return set(row['Диагноз'] for row in dataset)


def normalize_value(value, field_name):
    field = field_map.get(field_name)
    min, max = field.valid_range
    return (float(value) - min) / (max - min)


def normalize_dataset(dataset):
    normalized = []
    for row in dataset:
        normalized_row = {}
        for field_name, value in row.items():
            if field_name in text_fields:
                pass
            elif field_name in field_map:
                new_value = normalize_value(value, field_name)
                if not (0 <= new_value <= 1):
                    raise Exception("something went wrong in normalization, value doesn't fit")
                value = new_value
            else:
                raise Exception("unknown field '%s'" % field_name)
            normalized_row[field_name] = value
        normalized.append(normalized_row)
    return normalized


def form_dataset(csv_component_paths):
    dataset = []
    for csvpath in csv_component_paths:
        part = parse_dirty_dataset(csvpath)
        dataset.extend(part)

    return dataset


def write_dataset_csv(dataset, path):
    with open(path, 'w') as csvfile:
        fieldnames = dataset[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in dataset:
            writer.writerow(row)


def write_dataset_json(dataset, normalized_dataset, path):
    dataset_j = {}
    meta = {}
    meta['size'] = len(dataset)
    meta['diagnoses'] = list(get_diagnoses(dataset))
    meta['fields'] = [
        dict(name=f.name,
             type='float',
             prettyName=f.pretty_name,
             validRange=dict(min=f.valid_range[0], max=f.valid_range[1]))
        for f in fields
    ] + [
        dict(name=tf,
             type='text',
             prettyName=tf)
        for tf in text_fields
    ]

    dataset_j['meta'] = meta
    dataset_j['dataset'] = dataset
    dataset_j['normalizedDataset'] = normalized_dataset

    with open(path, 'w') as jsonfile:
        jsonfile.write(json.dumps(dataset_j, indent=4, ensure_ascii=False))


def main():
    csvs = [
        'peritonitis.csv',
        'appendicitis.csv',
        'hepatitis.csv',
    ]
    dataset = form_dataset(csvs)
    check_dataset(dataset)

    normalized_dataset = normalize_dataset(dataset)
    check_normalized_dataset(normalized_dataset)

    shuffle(dataset)
    shuffle(normalized_dataset)

    write_dataset_csv(dataset, 'dataset.csv')
    write_dataset_csv(normalized_dataset, 'dataset-normalized.csv')
    write_dataset_json(dataset, normalized_dataset, 'dataset.json')
    normalize_dataset(dataset)


if __name__ == '__main__':
    main()
