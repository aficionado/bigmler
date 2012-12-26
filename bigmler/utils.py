#!/usr/bin/env python
#
# Copyright 2012 BigML
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Utilities for BigMLer

"""
from __future__ import absolute_import

import csv
import fileinput
import ast
import glob
import os
import sys

try:
    import simplejson as json
except ImportError:
    import json

import bigml.api
from bigml.multimodel import combine_predictions

PAGE_LENGTH = 200
ATTRIBUTE_NAMES = ['name', 'label', 'description']


def read_description(path):
    """Reads a text description from a file.

    """
    lines = ''
    for line in fileinput.input([path]):
        lines += line
    return lines


def read_field_attributes(path):
    """Reads field attributes from a csv file to update source fields.

    A column number and a list of attributes separated by a comma per line.
    The expected structure is:
    column number, name, label, description

    For example:

    0,'first name','label for the first field','fist field full description'
    1,'last name','label for the last field','last field full description'

    """
    field_attributes = {}
    try:
        attributes_reader = csv.reader(open(path, "U"), quotechar="'")
    except IOError:
        sys.exit("Error: cannot read field attributes %s" % path)

    for row in attributes_reader:
        try:
            attributes = {}
            if len(row) > 1:
                for index in range(0, len(row) - 1):
                    attributes.update({ATTRIBUTE_NAMES[index]: row[index + 1]})
                field_attributes.update({
                    int(row[0]): attributes})
        except ValueError:
            pass
    return field_attributes


def read_types(path):
    """Types to update source fields types.

    A column number and type separated by a comma per line.

    For example:

    0, 'categorical'
    1, 'numeric'

    """
    types_dict = {}
    for line in fileinput.input([path]):
        try:
            pair = ast.literal_eval(line)
            types_dict.update({
                pair[0]: pair[1]})
        except SyntaxError:
            pass
    return types_dict


def read_models(path):
    """Reads model ids from a file.

    For example:

    model/50974922035d0706da00003d
    model/509748b7035d0706da000039
    model/5097488b155268377a000059

    """
    models = []
    for line in fileinput.input([path]):
        models.append(line.rstrip())
    return models


def read_dataset(path):
    """Reads dataset id from a file.

    For example:

    dataset/50978822035d0706da000069

    """
    datasets = []
    for line in fileinput.input([path]):
        datasets.append(line.rstrip())
    return datasets[0]


def read_json_filter(path):
    """Reads a json filter from a file.

    For example:

    [">", 3.14, ["field", "000002"]]

    """
    json_data = open(path)
    json_filter = json.load(json_data)
    json_data.close()
    return json_filter


def read_lisp_filter(path):
    """Reads a lisp filter from a file.

    For example:

    (> (/ (+ (- (field "00000") 4.4)
            (field 23)
            (* 2 (field "Class") (field "00004")))
       3)
       5.5)

    """
    return read_description(path)


def read_votes(dirs_list, path):
    """Reads a list of directories to look for votes.

    If model's prediction files are found, they are retrieved to be combined.
    """
    file_name = "%s%scombined_predictions" % (path,
                                              os.sep)
    check_dir(file_name)
    group_predictions = open(file_name, "w", 0)
    current_directory = os.getcwd()
    for directory in dirs_list:
        directory = os.path.abspath(directory)
        os.chdir(directory)
        predictions_files = []
        for predictions_file in glob.glob("model_*_predictions.csv"):
            predictions_files.append("%s%s%s" % (os.getcwd(),
                                     os.sep, predictions_file))
            group_predictions.write("%s\n" % predictions_file)
        os.chdir(current_directory)
    group_predictions.close()
    return predictions_files


def list_source_ids(api, query_string):
    """Lists BigML sources filtered by `query_string`.

    """
    q_s = 'status.code=%s;limit=%s;%s' % (
          bigml.api.FINISHED, PAGE_LENGTH, query_string)
    sources = api.list_sources(q_s)
    ids = ([] if sources['objects'] is None else
           [obj['resource'] for obj in sources['objects']])
    while (not sources['objects'] is None and
          (sources['meta']['total_count'] > (sources['meta']['offset'] +
           sources['meta']['limit']))):
        offset = sources['meta']['offset'] + PAGE_LENGTH
        q_s = 'status.code=%s;offset=%s;limit=%s;%s' % (
              bigml.api.FINISHED, offset, PAGE_LENGTH, query_string)
        sources = api.list_sources(q_s)
        ids.extend(([] if sources['objects'] is None else
                   [obj['resource'] for obj in sources['objects']]))
    return ids


def list_dataset_ids(api, query_string):
    """Lists BigML datasets filtered by `query_string`.

    """
    q_s = 'status.code=%s;limit=%s;%s' % (
          bigml.api.FINISHED, PAGE_LENGTH, query_string)
    datasets = api.list_datasets(q_s)
    ids = ([] if datasets['objects'] is None else
           [obj['resource'] for obj in datasets['objects']])
    while (not datasets['objects'] is None and
          (datasets['meta']['total_count'] > (datasets['meta']['offset'] +
           datasets['meta']['limit']))):
        offset = datasets['meta']['offset'] + PAGE_LENGTH
        q_s = 'status.code=%s;offset=%s;limit=%s;%s' % (
              bigml.api.FINISHED, offset, PAGE_LENGTH, query_string)
        datasets = api.list_datasets(q_s)
        ids.extend(([] if datasets['objects'] is None else
                   [obj['resource'] for obj in datasets['objects']]))
    return ids


def list_model_ids(api, query_string):
    """Lists BigML models filtered by `query_string`.

    """
    q_s = 'status.code=%s;limit=%s;%s' % (
          bigml.api.FINISHED, PAGE_LENGTH, query_string)
    models = api.list_models(q_s)
    ids = ([] if models['objects'] is None else
           [obj['resource'] for obj in models['objects']])
    while (not models['objects'] is None and
          (models['meta']['total_count'] > (models['meta']['offset'] +
           models['meta']['limit']))):
        offset = models['meta']['offset'] + PAGE_LENGTH
        q_s = 'status.code=%s;offset=%s;limit=%s;%s' % (
              bigml.api.FINISHED, offset, PAGE_LENGTH, query_string)
        models = api.list_models(q_s)
        ids.extend(([] if models['objects'] is None else
                   [obj['resource'] for obj in models['objects']]))
    return ids


def list_prediction_ids(api, query_string):
    """Lists BigML predictions filtered by `query_string`.

    """
    q_s = 'status.code=%s;limit=%s;%s' % (
          bigml.api.FINISHED, PAGE_LENGTH, query_string)
    predictions = api.list_predictions(q_s)
    ids = ([] if predictions['objects'] is None else
           [obj['resource'] for obj in predictions['objects']])
    while (not predictions['objects'] is None and
          (predictions['meta']['total_count'] > (predictions['meta']['offset']
           + predictions['meta']['limit']))):
        offset = predictions['meta']['offset'] + PAGE_LENGTH
        q_s = 'status.code=%s;offset=%s;limit=%s;%s' % (
              bigml.api.FINISHED, offset, PAGE_LENGTH, query_string)
        predictions = api.list_predictions(q_s)
        ids.extend(([] if predictions['objects'] is None else
                   [obj['resource'] for obj in predictions['objects']]))
    return ids


def combine_votes(votes_files, to_prediction, to_file, method='plurality'):
    """Combines the votes found in the votes' files and stores predictions.

    """
    votes = []
    for votes_file in votes_files:
        index = 0
        for row in csv.reader(open(votes_file, "U")):
            prediction = to_prediction(row[0])
            if index > (len(votes) - 1):
                votes.append({prediction: []})
            if not prediction in votes[index]:
                votes[index][prediction] = []
            votes[index][prediction].append(float(row[1]))
            index += 1

    check_dir(to_file)
    output = open(to_file, 'w', 0)
    for predictions in votes:
        write_prediction(predictions, method, output)
    output.close()


def delete(api, delete_list):
    """ Deletes the resources given in the list.

    """
    delete_functions = {bigml.api.SOURCE_RE: api.delete_source,
                        bigml.api.DATASET_RE: api.delete_dataset,
                        bigml.api.MODEL_RE: api.delete_model,
                        bigml.api.PREDICTION_RE: api.delete_prediction}
    for resource_id in delete_list:
        for resource_type in delete_functions:
            try:
                bigml.api.get_resource(resource_type, resource_id)
                delete_functions[resource_type](resource_id)
                break
            except ValueError:
                pass


def check_dir(path):
    """Creates a directory if it doesn't exist

    """
    directory = os.path.dirname(path)
    if len(directory) > 0 and not os.path.exists(directory):
        os.makedirs(directory)
        directory_log = open(".bigmler_dirs", "a", 0)
        directory_log.write("%s\n" % os.path.abspath(directory))
        directory_log.close()
    return directory


def write_prediction(predictions, method, output=sys.stdout):
    """Writes the final combined prediction to the required output

    """
    prediction = combine_predictions(predictions, method)
    if isinstance(prediction, basestring):
        prediction = prediction.encode("utf-8")
    output.write("%s\n" % prediction)
    output.flush()


def tail(file_handler, window=1):
    """Returns the last n lines of a file.

    """
    bufsiz = 1024
    file_handler.seek(0, 2)
    file_bytes = file_handler.tell()
    size = window
    block = -1
    data = []
    while size > 0 and bytes > 0:
        if (file_bytes - bufsiz > 0):
            # Seek back one whole bufsiz
            file_handler.seek(block * bufsiz, 2)
            # read BUFFER
            data.append(file_handler.read(bufsiz))
        else:
            # file too small, start from begining
            file_handler.seek(0, 0)
            # only read what was not read
            data.append(file_handler.read(bytes))
        lines_found = data[-1].count('\n')
        size -= lines_found
        file_bytes -= bufsiz
        block -= 1
    return (''.join(data).splitlines()[-window:])


def get_log_reversed(file_name, stack_level=0):
    """Reads the line of a log file that has the chosen stack_level

    """
    lines_list = tail(open(file_name, "r"), window=(stack_level + 1))
    return lines_list[0]


def is_source_created(path, api):
    """Reads the source id from the source file in the path directory

    """
    source_id = None
    try:
        source_file = open("%s%ssource" % (path, os.sep))
        source_id = source_file.readline().strip()
        try:
            source_id = api.get_source_id(source_id)
            return True, source_id
        except ValueError:
            return False, None
    except IOError:
        return False, None


def is_dataset_created(path, api):
    """Reads the dataset id from the dataset file in the path directory

    """
    dataset_id = None
    try:
        dataset_file = open("%s%sdataset" % (path, os.sep))
        dataset_id = dataset_file.readline().strip()
        try:
            dataset_id = api.get_dataset_id(dataset_id)
            return True, dataset_id
        except ValueError:
            return False, None
    except IOError:
        return False, None


def are_models_created(path, number_of_models, api):
    """Reads the model ids from the models file in the path directory

    """
    model_ids = []
    try:
        models_file = open("%s%smodels" % (path, os.sep))
        for line in models_file:
            model = line.strip()
            try:
                model_id = api.get_model_id(model)
                model_ids.append(model_id)
            except ValueError:
                return False, model_ids
        if len(model_ids) == number_of_models:
            return True, model_ids
        else:
            return False, model_ids
    except IOError:
        return False, model_ids


def are_predictions_created(predictions_file, number_of_tests):
    """Reads the predictions from the predictions file in the path directory

    """
    predictions = file_number_of_lines(predictions_file)
    if predictions != number_of_tests:
        os.remove(predictions_file)
        return False
    return True


def checkpoint(function, *args):
    """Tests function on path

    """
    return function(*args)


def file_number_of_lines(file_name):
    """Counts the number of lines in a file

    """
    try:
        with open(file_name) as file_handler:
            for item in enumerate(file_handler):
                pass
        return item[0] + 1
    except IOError:
        return 0