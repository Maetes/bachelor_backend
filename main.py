from flask import Flask, json, jsonify, request, send_file
import sqlalchemy
from sqlalchemy.ext.declarative import DeclarativeMeta
from multiprocessing import Process
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.orm import load_only
from algorithms import Algorithms
import sys, os
from database import db, History


max_threads = 1
running = {}
finished = []
queue = []
waiting_for_data = {}
queue_list = set()

#import from https://stackoverflow.com/questions/5022066/how-to-serialize-sqlalchemy-result-to-json
class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_ADDR')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_timeout': 3600}
    # app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True, "pool_recycle": 300,}
    with app.app_context():
        db.init_app(app)
    CORS(app)
    return app

app = create_app()

#app.config('CORS_HEADERS') = 'Content-Type'

# MULTITHREADING FUNCTIONS
# https://stackoverflow.com/questions/64663548/python-flask-spawn-jobs-with-multiprocessing
def finish_job(job_id):
    finished.append(job_id)
    last = running.pop(job_id)
    last.close()
    if len(queue) > 0:
        next_job = queue.pop()
        queue_list.remove(next_job[0])
        start_job(next_job)

def start_job(job=None):
    if job is None:
        job = queue.pop()
        queue_list.remove(job[0])
    task_cb = Process(target=job[1], args=(job[0],))
    task_cb.start()
    print('started thread')
    running[job[0]] = task_cb

def submit_job_local(job_id, job_algo):
# check not too many processing jobs
    if len(running) >= max_threads:
        queue.append((job_id, job_algo))
        queue_list.add(job_id)
        status = 'QUEUED'
    else:
        start_job((job_id, job_algo))
        status = 'RUNNING'
    return status, job_id

def remove_finished():
    for j in list(running.keys()):
        if not running[j].is_alive():
            finish_job(j)

@app.route("/")
def welcome():
    return "<p>This is a API for my Bachelor thesis. It runs three frequent pattern algorithms and generated based on them their respective association rules.</p>"

@app.route("/history")
def getHistory():
    result = History.query.with_entities(History.id,History.Zeitstempel, History.Algorithmus, History.Dataset, History.Support, History.Confidence)
    asd = [dict(c) for c in result]
    # for c in result:
    #     for d in c:
    #         if(d == '0.22'):
    #             print(d.to_dict())
    #     print(c.to_dict())
    # asd = [c.to_dict() for c in result]
    # return json.dumps(asd.to_dict(only=('Zeitstempel', 'Algorithmus', 'Dataset', 'Support', 'Confidence')))
    return json.dumps(asd, cls=AlchemyEncoder)

@app.route("/getID/<path:id>", methods=['GET'])
def getId(id):
    id = str(id)
    result = History.query.get(id)
    return json.dumps(result, cls=AlchemyEncoder)

@app.route("/getDataset/<path:dataset>", methods=['GET'])
def getDataset(dataset):
    print(os.path.dirname(os.path.realpath(__file__)) + "/datasets/" + dataset)
    if dataset is None:
        return 'Dataset nicht angegeben', 500
    try:
        return send_file(os.path.dirname(os.path.realpath(__file__)) + "/datasets/"+dataset, as_attachment=True)
    except Exception as e:
        print(e)
        return 'Dataset nicht gefunden', 404


@app.route("/check/<uuid:job_id>", methods=['GET'])
def check_status(job_id: uuid):
    job_id = str(job_id)
    remove_finished()
    if job_id in running:
        r = 'RUNNING'
    elif job_id in queue_list:
        r = 'QUEUED'
    elif job_id in finished:
        r = 'COMPLETED'
    else:
        r = 'FAILED'
    return r, 200

@app.route("/run/<path:algo>")
def runAlgos(algo):
    job_id = str(uuid.uuid4())

    dataDir = os.path.dirname(os.path.realpath(__file__)) + "/datasets/"
    
    algos = {"Beispieldatenset": "Beispieldatenset.txt", "Aldi_Ausgangsbasis": "Aldi_Ausgangsbasis.txt", "Rewe_Ausgangsbasis": "Rewe_Ausgangsbasis.txt", "Aldi_Transaktionen":"Aldi_Transaktionen.txt", "Rewe_Transaktionen":"Rewe_Transaktionen.txt", "Aldi_Warenkorb":"Aldi_Warenkorb.txt", "Rewe_Warenkorb":"Rewe_Warenkorb.txt","Aldi_häufigeItemsets":"Aldi_häufigeItemsets.txt","Rewe_häufigeItemsets":"Rewe_häufigeItemsets.txt", "Aldi_Items":"Aldi_Items.txt", "Rewe_Items":"Rewe_Items.txt"}

    dataset=request.args.get('data')
    datasetFile = algos[dataset]
    support = float(request.args.get('support'))
    confidence = float(request.args.get('confidence',0))
    executr = Algorithms(algorithm=algo, confidence=confidence, data=dataDir+datasetFile, support=support)

    if(confidence > 0.0):
        status = submit_job_local(job_id, executr.runFPandAR)
    else:
        status = submit_job_local(job_id, executr.runFP)
    return status[1], 200

@app.route("/results/<path:jobid>")
def mapper(jobid):
        # if str(jobid) not in finished:
        #     return 'job id not found', 404
        file_path = os.path.join('results', jobid+'.json')
        print('FILEPATH!!!!', file_path, os.path.isfile(file_path))
        if not os.path.isfile(file_path):
            return 'file not found', 404
        erg = json.load(open(file_path,"r",encoding="utf-8"))
        print(json.dumps(erg['config']['Datenset'], ensure_ascii=False).encode('utf-8'))
        if (erg == 'Keine FrequentItemsets gegunden!'):
            return erg, 409
        if(erg['config']['Konfidenz'] != 0):
            try:
                ins = History(Algorithmus=json.dumps(erg['config']['Algorithmus']), Dataset=json.dumps(erg['config']['Datenset'], ensure_ascii=False).encode('utf-8'), Support=json.dumps(erg['config']['Support']), Confidence=json.dumps(erg['config']['Konfidenz']), Association_Start_CPU=json.dumps(erg['start']['association']['cpu']), Association_Start_Memory=json.dumps(erg['start']['association']['memory']), FrequentItems_Start_CPU=json.dumps(erg['start']['freqItems']['cpu']), FrequentItems_Start_Memory=json.dumps(erg['start']['freqItems']['memory']), Association_Ende_CPU=json.dumps(erg['end']['association']['cpu']), Association_Ende_Memory=json.dumps(erg['end']['association']['memory']), Association_Ende_Zeit=json.dumps(erg['end']['association']['time']), Association_Ende_Association_rules=erg['end']['association']['asso'], FrequentItems_Ende_CPU=json.dumps(erg['end']['freqItems']['cpu']), FrequentItems_Ende_Memory=json.dumps(erg['end']['freqItems']['memory']), FrequentItems_Ende_Zeit=json.dumps(erg['end']['freqItems']['time']), FrequentItems_Ende_Frequent_items=erg['end']['freqItems']['freq'])
                db.session.add(ins)
                db.session.commit()
            except sqlalchemy.exc.OperationalError as err:
                return jsonify('Server Error, Ergebnis zu groß für Datenbank!'), 500
            except:
                return jsonify(erg)
        else:
            try:
                ins = History(Algorithmus=json.dumps(erg['config']['Algorithmus']), Dataset=json.dumps(erg['config']['Datenset'], ensure_ascii=False).encode('utf-8'), Support=json.dumps(erg['config']['Support']), FrequentItems_Start_CPU=json.dumps(erg['start']['freqItems']['cpu']), FrequentItems_Start_Memory=json.dumps(erg['start']['freqItems']['memory']), FrequentItems_Ende_CPU=json.dumps(erg['end']['freqItems']['cpu']), FrequentItems_Ende_Memory=json.dumps(erg['end']['freqItems']['memory']), FrequentItems_Ende_Zeit=json.dumps(erg['end']['freqItems']['time']), FrequentItems_Ende_Frequent_items=erg['end']['freqItems']['freq'])
                db.session.add(ins)
                db.session.commit()
            except sqlalchemy.exc.OperationalError as err:
                return jsonify('Server Error, Ergebnis zu groß für Datenbank!'), 500
            except:
                return jsonify('Could not connect to the Database'), 500
        return jsonify(erg)
        #         returner = {
        #             'start': {
        #                 'freqItems': {
        #                     'cpu': freq.start.cpu,
        #                     'memory': freq.start.memory
        #                 },
        #                 'association': {
        #                     'cpu': asso.start.cpu if asso else None,
        #                     'memory': asso.start.memory if asso else None
        #                 }
        #             },
        #             'end': {
        #                 'freqItems': {
        #                     'freq': freq.end.freq.to_json(orient='records') if freq.end.freq.empty != True else None,
        #                     'cpu': freq.end.cpu,
        #                     'memory': freq.end.memory,
        #                     'time': [freq.end.time]
        #                 },
        #                 'association': {
        #                     'asso': asso.end.asso.to_json(orient='records') if asso else None,
        #                     'cpu': asso.end.cpu if asso else None,
        #                     'memory': asso.end.memory if asso else None,
        #                     'time': [asso.end.time] if asso else None,
        #                 }
        #             }
        #         }
        #         ins = History(Algorithmus=json.dumps(algo), Dataset=json.dumps(dataset), Support=json.dumps(support), Confidence=json.dumps(confidence), Association_Start_CPU=json.dumps(asso.start.cpu), Association_Start_Memory=json.dumps(asso.start.memory), FrequentItems_Start_CPU=json.dumps(freq.start.cpu), FrequentItems_Start_Memory=json.dumps(freq.start.memory), Association_Ende_CPU=json.dumps(asso.end.cpu), Association_Ende_Memory=json.dumps(asso.end.memory), Association_Ende_Zeit=json.dumps(asso.end.time), Association_Ende_Association_rules=asso.end.asso.to_json(orient='records'), FrequentItems_Ende_CPU=json.dumps(freq.end.cpu), FrequentItems_Ende_Memory=json.dumps(freq.end.memory), FrequentItems_Ende_Zeit=json.dumps(freq.end.time), FrequentItems_Ende_Frequent_items=freq.end.freq.to_json(orient='records'))
        #         db.session.add(ins)
        #         db.session.commit()
        #     else:
        #         returner = 'Keine Frequent Itemsets gefunden' 
        #     return jsonify(returner)
        # except ValueError as err:
        #     return err.args[0]
    # else:
    #     try:
    #         eval = executr.runFP()
    #         if eval.end.freq.empty != True:
    #             returner = {
    #                 'start': {
    #                     'freqItems': {
    #                         'cpu': eval.start.cpu,
    #                         'memory': eval.start.memory
    #                     }
    #                 },
    #                 'end':{
    #                     'freqItems': {
    #                         'freq': eval.end.freq.to_json(orient='records'),
    #                         'cpu': eval.end.cpu,
    #                         'memory': eval.end.memory,
    #                         'time': eval.end.time
    #                     }
    #                 }
    #             }
    #             ins = History(Algorithmus=json.dumps(algo), Dataset=json.dumps(dataset), Support=json.dumps(support), FrequentItems_Start_CPU=json.dumps(eval.start.cpu), FrequentItems_Start_Memory=json.dumps(eval.start.memory), FrequentItems_Ende_CPU=json.dumps(eval.end.cpu), FrequentItems_Ende_Memory=json.dumps(eval.end.memory), FrequentItems_Ende_Zeit=json.dumps(eval.end.time), FrequentItems_Ende_Frequent_items=eval.end.freq.to_json(orient='records'))
    #             db.session.add(ins)
    #             db.session.commit()
    #         else:
    #             returner = 'Keine Frequent Itemsets gefunden' 
    #         return jsonify(returner)
    #     except ValueError as err:
    #             return err.args[0]