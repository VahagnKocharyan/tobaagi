#!/usr/bin/python


import sys
from typing import Dict
import pymysql
from config import *
from datetime import datetime
import pymongo

class TobaDbConnector:

    """A  database connector class"""

    def __init__(self):
        """Constructor"""
        self.db = None
        self.record_id = None
        self.account_id=None
        self.mongo=None
        self.mongodb=None

    def connect(self):
        """ Database connector function"""
        self.db = pymysql.connect(host=DBHOST, user=DBUSER,
                                  passwd=DBPASSWD, db=DBNAME)
    def mongoconnect(self):
        self.mongo=pymongo.MongoClient("mongodb://localhost:27017/")
        self.mongodb = self.mongo.voip

    def mongodisconnect(self):
        self.mongo.close()

    def get_timeouts(self):
        """Retrieves unimrcp timeouts from unimrcptimeouts table"""
        result = dict()
        result['status'] = False
        try:
            self.connect()

            db = self.db.cursor()

            db.execute(
                """SELECT SINGLE_UTTERANCE,SPEECH_COMPLETE_TIMEOUT,SPEECH_INCOMPLETE_TIMEOUT,NOINPUT_TIMEOUT,INPUT_TIMEOUT,DTMF_INTERDIGIT_TIMEOUT  FROM UNIMRCPTIMEOUTS  """ )
            record = db.fetchone()
            if record:
                result['status'] = True
                result['SINGLE_UTTERANCE'] = record[0]
                result['SPEECH_COMPLETE_TIMEOUT'] = record[1]
                result['SPEECH_INCOMPLETE_TIMEOUT'] = record[2]
                result["NOINPUT_TIMEOUT"]= record[3]
                result["INPUT_TIMEOUT"]= record[4]
                result["DTMF_INTERDIGIT_TIMEOUT"]= record[5]
                
                
            else:
                result['error_cause'] = 'Unrecognized'
            db.close()

        except pymysql.Error as e:
            result['error_cause'] = 'MySQL Error [%d]: %s' % (
                e.args[0], e.args[1])
        except:
            result['error_cause'] = 'Unknown error occurred'

        return result

    def get_prompts(self,promptname):
        result = dict()
        result['status'] = False
        result['account']=dict()
        try:
            self.mongoconnect()
            result=self.mongodb.prompts.find_one({"PROMPTNAME":promptname})
            result['status'] = True
            self.mongodisconnect()
        except Exception as e:
            result['error_cause'] = 'Mongodb Error %s' % (e)
        except:
            result['error_cause'] = 'Unknown error occurred'
        return result


    def get_caller_info(self, callerid):
        """Retrieves caller information from mongodb account"""
        result = dict()
        result['status'] = False
        result['account']=dict()
        try:
            self.mongoconnect()
            # result=self.mongodb.accounts.find_one({"phone":"37498000662","isVerified":"yes"},)
            result['account']=list(self.mongodb.accounts.aggregate([{"$match":{"phone":callerid,"isVerified":"yes"}},{
                "$lookup": {
                    "from": "languages",
                    "localField": "languages.primary",
                    "foreignField": "_id",
                    "as": "languages.primary"
                },
            },{
                "$lookup": {
                    "from": "languages",
                    "localField": "languages.guest",
                    "foreignField": "_id",
                    "as": "languages.guest"
                }
            },{
                "$lookup": {
                    "from": "users",
                    "localField": "user.id",
                    "foreignField": "_id",
                    "as": "name.username"
                }
            },{
                "$lookup": {
                    "from": "prompts",
                    "localField": "Prompts",
                    "foreignField": "_id",
                    "as": "Prompts"
                }
            },{
                "$lookup": {
                    "from": "calllogs",
                    "localField": "Calllogs",
                    "foreignField": "_id",
                    "as": "Calllogs"
                }
            },{
                "$project": {
                    "name.full":1,
                    "name.username.username":1,
                    "phone":1,
                    "server":1,
                    "languages":1,
                    "lastcalllogs":{ "$last": "$Calllogs" },
                    
                    "Prompts": {
                        "$arrayToObject": {
                            "$map": {
                            "input": "$Prompts",
                            "as": "pair",
                            "in": ["$$pair.PROMPTNAME", "$$pair.PROMPTTEXT"]
                            }
                        }
                    }
                }
            }]))[0]
            result['status'] = True
            self.account_id=result['account']['_id']
            self.CallId=result['account']['lastcalllogs']['CallID']
            self.mongodisconnect()
            # print(result)
            # result.cursor.populate("languages.primary","languages")


        except Exception as e:
            result['error_cause'] = 'Mongodb Error %s' % (e)
        except:
            result['error_cause'] = 'Unknown error occurred'
        # print(result)
        return result



    

    def add_record(self,data,calllogsGLOBALID):
        """Inserts a new record with call data"""
        result = dict()
        result['status'] = False
        try:
            self.mongoconnect()
            # print(data)
            if calllogsGLOBALID:
                results=self.mongodb.calllogs.find_one({'CallID':calllogsGLOBALID})
                if results:
                    self.record_id=results['_id']

            if not self.record_id:
                result['calllogs'] = self.mongodb.calllogs.insert_one(data)
                self.record_id = result['calllogs'].inserted_id
                myquery = { "_id":  self.account_id}
                newvalues = { "$push": { "Calllogs":self.record_id } }
                result['utterancelogs'] = self.mongodb.accounts.update_one(myquery, newvalues)

            self.mongodisconnect()

            result['status'] = True
            result['string'] = 'Your query is successfully committed, record_id is %s' % self.record_id

        except Exception as e:
            result['error_cause'] = 'Mongodb Error %s' % (e)
        except:
            result['error_cause'] = 'Unknown error occurred'
        # print(result)
        return result





    def set_duration(self, duration):
        """Updates duration field in the current record"""
        result = dict()
        result['status'] = False
        try:
            self.mongoconnect()

            myquery = { "_id":  self.record_id}
            newvalues = { "$set": { "Duration":str(duration) } }
            result['duration']=self.mongodb.calllogs.update_one(myquery, newvalues)
            self.mongodisconnect()

            result['status'] = True
            result['string'] = 'duration successfully updated'

        except Exception as e:
            result['error_cause'] = 'Mongodb Error %s' % (e)
        except:
            result['error_cause'] = 'Unknown error occurred'
        # print(result)
        return result

    def update_status(self, status):
        """Updates dialstatus field in the current record"""
        result = dict()
        result['status'] = False
        try:
            self.mongoconnect()

            myquery = { "_id":  self.record_id}
            newvalues = { "$set": { "Status":status } }
            result['Status']=self.mongodb.calllogs.update_one(myquery, newvalues)
            self.mongodisconnect()


            result['status'] = True
            result['string'] = 'Dial status is updated '

        except Exception as e:
            result['error_cause'] = 'Mongodb Error %s' % (e)
        except:
            result['error_cause'] = 'Unknown error occurred'
        # print(result)
        return result


    def update_language(self, language):
        """Updates language field in the current record"""
        result = dict()
        result['status'] = False
        try:
            
            self.mongoconnect()
            myquery = { "_id":  self.record_id}
            newvalues = { "$set": { "SelectedGuestLanguageCode":language } }
            result['GuestLanguage']=self.mongodb.calllogs.update_one(myquery, newvalues)
            self.mongodisconnect()

            result['status'] = True
            result['string'] = 'GuestLanguage successfully updated'

        except Exception as e:
            result['error_cause'] = 'Mongodb Error %s' % (e)
        except:
            result['error_cause'] = 'Unknown error occurred'
        # print(result)
        return result


    def add_utterance(self, data):
        """Inserts a new utterance with interaction data"""
        result = dict()
        result['status'] = False
        
        if not self.record_id:
            result['error_cause'] = 'No record_id'
            return result

        try:
            self.mongoconnect()
            result['utterancelogs'] = self.mongodb.utterancelogs.insert_one(data)
            result['record_id'] = result['utterancelogs'].inserted_id
            myquery = { "_id":  self.account_id}
            newvalues = { "$push": { "Utterancelogs":result['record_id'] } }
            result['utterancelogs'] = self.mongodb.accounts.update_one(myquery, newvalues)
            myqueryc = { "_id":  self.record_id}
            newvaluesc = { "$push": { "Utterancelogs":result['record_id'] } }
            result['utterancelogs'] = self.mongodb.calllogs.update_one(myqueryc, newvaluesc)
            self.mongodisconnect()
            result['record_id']=self.record_id
            result['status'] = True
            result['string'] = 'your query is successfully committed and account %s Utterancelogs updated' % self.account_id

        except Exception as e:
            result['error_cause'] = 'Mongodb Error %s' % (e)
        except:
            result['error_cause'] = 'Unknown error occurred'
        # print(result)
        return result


# app=TobaDbConnector()
# # print(app.add_record(None,'03548635745cee617cd2325c675e1871@185.45.152.136:5060'))
# print(app.get_caller_info('37498000662'))
# calllogs = {    "AccountId": "not registered" ,
#                 "CallID":"not registered" ,
#                 "UserCLI":"not registered" ,
#                 "StartTime":
#                 "Duration":"Duration",
#                 "Status":"not registered" ,
#                 "From":"not registered" ,
#                 "UserAgent":"not registered" ,
#                 "PrimaryLanguage":"not registered" ,
#                 "SelectedGuestLanguageCode":"not registered" ,
#                 "ServerCountry": "not registered" 
#              }
# result = app.add_record(calllogs)
# print(result)