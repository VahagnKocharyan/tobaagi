#!/usr/bin/python3
"""
    Asterisk TEST AGI custom application 

    This script interacts with gsr and gss API via UniMRCP server.

    * Revision: 3
    * Date: jan 23, 2022
    * Vendor: Vahagn kocharyan kocharyan.vahagn@gmail.com
"""
from pickle import TRUE
import sys
from telnetlib import STATUS
import six
import os
from datetime import datetime,timezone,timedelta
from tokenize import Name
from tracemalloc import start
from typing import DefaultDict
from asterisk.agi import *
from translate import *
from polydb import *
from config import *
from composedatetime import *




class SpeechTranscriptionApp:

    """A class representing speech transcription application"""

    def __init__(self):
        """Constructor"""
        self.options = None
        self.prompt = ""
        self.language = None
        self.guest_language=None
        self.caller_info= None
        self.single_utterance=None
        self.alternative_languages = None
        self.lang_confirmation=False
        self.action= "Selectlanguage"
        self.interaction_count = 0
        self.status = None
        self.cause = None
        os.environ[TRANSLATEKEYTYPE] = TRANSLATEKEYPATH


    def get_callerid(self):
        """Retrieves caller id from Asterisk"""

        agi.verbose('callerid %s' % agi.env['agi_callerid'])
        caller_id=agi.env['agi_callerid']
        numeric_filter = filter(str.isdigit, caller_id)
        numeric_string = "".join(numeric_filter)
        return numeric_string

    def get_from_header(self):
        """Retrieves from header from Asterisk Sip invite request"""

        agi.verbose('from header %s' % agi.get_variable('From'))
        return agi.get_variable('From')

    def get_to_header(self):
        """Retrieves to header from Asterisk Sip invite request"""

        agi.verbose('to header %s' % agi.get_variable('To'))
        return agi.get_variable('To')

    def get_Contact_header(self):
        """Retrieves Contact header from Asterisk Sip invite request"""

        agi.verbose('Contact header %s' % agi.get_variable('Contact'))
        return agi.get_variable('Contact')

    def get_Call_ID_header(self):
        """Retrieves to Call-ID from Asterisk Sip invite request"""

        agi.verbose('Call-ID header %s' % agi.get_variable('Call_ID'))
        return agi.get_variable('Call_ID')

    def get_User_Agent_header(self):
        """Retrieves User_Agent header from Asterisk Sip invite request"""

        agi.verbose('User-Agent header %s' % agi.get_variable('User_Agent'))
        return agi.get_variable('User_Agent')
    
    def get_primary_language_header(self):
        """Retrieves x-primary-language header from Asterisk Sip invite request"""

        agi.verbose('x-primary-language %s' % agi.get_variable("Primary_language"))
        return agi.get_variable("Primary_language")

    def get_guest_language_header(self):
        """Retrieves x-guest-language header from Asterisk Sip invite request"""

        agi.verbose('x-guest-language header %s' % agi.get_variable("Guest_language"))
        return agi.get_variable("Guest_language")


    def transcribe_speech(self):
        """Performs a streaming speech transcription"""
        self.set_call_duration(self.store_duration())
        self.options=self.compose_speech_options()
        if self.action=="Starttalking" or self.action=="translation":
            self.grammars = "%s" % (self.compose_speech_grammar())
        else:
            
            self.grammars = "%s" % (self.compose_dtmf_grammar())
        self.store_poly_interaction()
        self.synth_and_recog()
        self.store_caller_interaction()

    def synth_and_recog(self):
        """This is an internal function which calls SynthAndRecog"""
        if not self.prompt:
            self.prompt = ' '
        args = "\\\"%s\\\",\\\"%s\\\",%s" % (
            self.prompt, self.grammars, self.options)
        agi.set_variable('RECOG_STATUS', '')
        agi.set_variable('RECOG_COMPLETION_CAUSE', '')
        # self.action = None
        agi.appexec('SynthandRecog', args)
        self.status = agi.get_variable('RECOG_STATUS')
        agi.verbose('got status %s' % self.status)
        if self.status == 'OK':
            self.cause = agi.get_variable('RECOG_COMPLETION_CAUSE')
            agi.verbose('got completion cause %s' % self.cause)
        else:
            agi.verbose('recognition completed abnormally')

    def compose_speech_grammar(self):
        """Composes a built-in speech grammar"""
        grammar = 'builtin:speech/transcribe'
        separator = '?'

        if self.single_utterance:
            grammar = self.append_grammar_parameter(
                grammar, "single-utterance", self.single_utterance, separator)
            separator = ';'

        if self.alternative_languages:
            grammar = self.append_grammar_parameter(
                grammar, "alternate-languages", self.alternative_languages['Rcode'].lower(), separator)
            separator = ';'

        return grammar

    def compose_dtmf_grammar(self):
        """Composes a built-in DTMF grammar"""
        grammar = 'builtin:dtmf/digits'
        return grammar

    def append_grammar_parameter(self, grammar, name, value, separator):
        """Appends a name/value parameter to the specified grammar"""
        grammar += "%s%s=%s" % (separator, name, value)

        return grammar

    def append_option_parameter(self, options, name, value, separator):
        """Appends a name/value parameter to the specified grammar"""
        options += "%s%s=%s" % (separator, name, value)
        
        return options
    

    def compose_speech_options1(self):
        """Composes speech options"""

        if self.action=="Starttalking":
            options = 'plt=1&b=1&sct=1000&sint=15000&nit=10000'
        else:
            options = 'plt=1&dit=1000&b=1&sct=600&sint=1000&nit=3000'

        separator = '&'
        if self.language:
            agi.verbose('set language to  %s' % self.language)
            options = self.append_option_parameter(
                options, "spl",self.language['Rcode'], separator)

            options = self.append_option_parameter(
                options, "vv", self.language['Scode'], separator)
            
            
        return options

    def compose_speech_options(self):
        """Composes speech options"""
        options=poly_db.get_timeouts()
        currentspeechoptions=None
        currentdtmfoptions=None
        defauloptions='plt=1&b=1'
        if options['status'] == True:
            agi.verbose('database -> got timeouts info%s' % options)
            separator = '&'
            currentspeechoptions = self.append_option_parameter(
                defauloptions, "sct",options['SPEECH_COMPLETE_TIMEOUT'], separator)

            currentspeechoptions = self.append_option_parameter(
                currentspeechoptions, "sint", options['SPEECH_INCOMPLETE_TIMEOUT'], separator)

            currentspeechoptions = self.append_option_parameter(
                currentspeechoptions, "nit", options['NOINPUT_TIMEOUT'], separator)

            currentspeechoptions = self.append_option_parameter(
                currentspeechoptions, "t", options['INPUT_TIMEOUT'], separator)
             
            currentdtmfoptions= self.append_option_parameter(
                defauloptions, "dit", options['DTMF_INTERDIGIT_TIMEOUT'], separator)

            if self.action=="Starttalking":
                # options = 'plt=1&b=1&sct=1000&sint=15000&nit=10000'
                self.single_utterance=options['SINGLE_UTTERANCE']
                options=currentspeechoptions
                
            else:
                # options = 'plt=1&dit=1000&b=1'
                options=currentdtmfoptions
            
        else:
            agi.verbose('database %s' % options['error_cause'])

        separator = '&'

        if self.language:
            agi.verbose('set language to  %s' % self.language)
            options = self.append_option_parameter(
                options, "spl",self.language['Rcode'], separator)

            options = self.append_option_parameter(
                options, "vv", self.language['Scode'], separator)
            
            
        return options
        



    def get_transcribed(self):
        """get transcription"""

        transcription=agi.get_variable('RECOG_INSTANCE(0/0/StreamingRecognitionResult/alternatives/transcript)')
        agi.verbose('got transcription %s' % transcription)

        return transcription

    def get_dtmf(self):
        """get dtmf"""
        dtmf=agi.get_variable('RECOG_INSTANCE(0/0)')
        agi.verbose('got dtmf %s' % dtmf)

        return dtmf

    def get_language_code(self):
        """get language code"""

        language_code=agi.get_variable('RECOG_INSTANCE(0/0/StreamingRecognitionResult/language_code)')
        agi.verbose('got transcribtion language_code %s' % language_code)

        return language_code


    def get_prompt(self,action):
        agi.verbose('i am heeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
        
        prompt_info = poly_db.get_prompt_info(action)
            # agi.verbose('database -> got prompt info%s' % prompt_info['status'])
        if prompt_info['status'] == True:
            agi.verbose('database -> got prompt info%s' % prompt_info)
            agi.verbose('got language->%s'%self.language['Tcode'])
            self.prompt=get_translation(prompt_info['PROMPTTEXT'],str(self.language['Tcode'])) 
            
        else:
            agi.verbose('database %s' % prompt_info['error_cause'])
    
    
    

    def get_caller_info(self):
        """Get caller info from db"""
        caller_info= poly_db.get_caller_info(self.get_callerid())
        if caller_info['status'] == True:
            
            agi.verbose('database -> current user primary language: %s ,current guest languages: %s' % (caller_info['primary_language'],caller_info['guest_languages']))
            self.caller_info=caller_info
            
            if self.caller_info['guest_languages']['R2']=='':
                self.alternative_languages=self.guest_language=self.get_language_info_from_db(self.caller_info['guest_languages']['R1'])
                self.action="Starttalking"

            primary_language_header=self.get_primary_language_header()
            guest_language_header = self.get_guest_language_header()
            if primary_language_header!="" and guest_language_header!="" :
               self.caller_info['primary_language']=primary_language_header
               self.alternative_languages=self.guest_language=self.get_language_info_from_db(guest_language_header)
               self.action="Starttalking"

            self.language=self.get_language_info_from_db(self.caller_info['primary_language'])          
            
        else:
            agi.verbose('database -> failed to get caller info:%s' % caller_info['error_cause'])
            self.action =caller_info['error_cause']
            self.language=dict()
            self.language['Tcode']='en' 

        self.add_db_record()
        
            


            
    def get_language_info_from_db(self,language):
        """get language data from polydb"""
        result=poly_db.get_language_info(language)
        if result['status'] == True:
            agi.verbose('got data from database')
            return result
        else:
            agi.verbose('database %s' % result['error_cause'])

    
        
       

    def translate_prompt(self):
        prompt= ""
        primary_language=self.get_language_info_from_db(self.caller_info['primary_language'])
        guest_language=self.guest_language
        transcribed=self.get_transcribed()
        if self.get_language_code()==guest_language['Rcode'].lower():
            agi.verbose('%s -> %s' %(transcribed,primary_language['Tcode']))
            prompt=get_translation(str(transcribed),primary_language['Tcode'])
            self.language=primary_language
            self.alternative_languages=guest_language

        if self.get_language_code()==primary_language['Rcode'].lower():
            agi.verbose('%s -> %s' %(transcribed,guest_language['Tcode']))
            prompt=get_translation(str(transcribed),guest_language['Tcode']) 
            self.language=guest_language
            self.options=self.compose_speech_options()
            self.alternative_languages=primary_language

        agi.verbose('current options->%s'% self.options)
        agi.verbose('current language : %s' %(self.language))
        agi.verbose('%s -> %s' %(transcribed,prompt))
        return prompt

    def translate_prompt2(self):
        prompt= ""
        transcribed=self.get_transcribed()
        
        if self.get_language_code()==self.guest_language['Rcode'].lower():
            self.language=self.alternative_languages
            agi.verbose(' %s -> %s' %(transcribed,self.language['Tcode']))
            prompt=get_translation(str(transcribed),self.language['Tcode'])

        if self.get_language_code()==self.language['Rcode'].lower():
            agi.verbose(' %s -> %s' %(transcribed,self.guest_language['Tcode']))
            prompt=get_translation(str(transcribed),self.guest_language['Tcode'])
            self.alternative_languages=self.language
            if self.language['Rcode']==self.language['Rcode']:
                self.language=self.guest_language
            
        agi.verbose('current options->%s'% self.options)
        agi.verbose('current language : %s' %(self.language))
        agi.verbose('%s -> %s' %(transcribed,prompt)) 

        return prompt




    def language_selection(self):
        agi.verbose('current prompt name -> %s' % self.action)
        
        if self.action=="Selectlanguage" or self.action=="Wrongselection" or self.action=="Confirmselection":
            dtmf=self.get_dtmf()
            key='R%s'%dtmf
            if key in self.caller_info['guest_languages']:
                language_code=self.caller_info['guest_languages'][key] 
                self.action="Confirmselection"      

                if not self.guest_language:
                    agi.verbose('selected language %s' % self.guest_language )
                    language_info=self.get_language_info_from_db(language_code)
                    self.guest_language=language_info

                agi.verbose('selected language %s' % self.guest_language )

                if self.guest_language['Rcode']==language_code:
                    if self.lang_confirmation==False:
                        self.lang_confirmation=True
                        agi.verbose(' guest language :%s to be confirmed: %s' % (self.guest_language,self.lang_confirmation))

                    elif self.lang_confirmation==True:
                        self.action="Starttalking"
                        agi.verbose('confirmed guest language -> %s' % self.guest_language)
                        self.alternative_languages=self.guest_language
                        self.update_call_guest_language(self.guest_language['Rcode'])
                            
                else:
                    
                    language_info=self.get_language_info_from_db(language_code)
                    self.guest_language=language_info
   
            else:
                self.lang_confirmation=False
                self.action="Wrongselection"

    def store_starttime(self):
        """Stores current time as starttime"""
        self.starttime=datetime.now(GMT).strftime('%m/%d/%Y %H:%M:%S.%f %Z%z')
        agi.verbose('start time -> %s' % self.starttime)

    def store_duration(self):
        """Stores duration"""     
        date_time =datetime.now(GMT).strftime('%m/%d/%Y %H:%M:%S.%f %Z%z')
        fmt = '%m/%d/%Y %H:%M:%S.%f %Z%z'
        tstamp1 = datetime.strptime(self.starttime, fmt)
        tstamp2 = datetime.strptime(date_time, fmt)
        td = tstamp2 - tstamp1

        
        duration = timedelta(seconds=int(td.total_seconds()))
        agi.verbose('endtime:%s - starttime: %s -> %s' %(tstamp2,tstamp1,duration ))

        return duration

    def add_db_record(self):
        """Stores interactions in a db record"""
        
        Status = self.action
        Duration =None
        
        id=None
        Name=None
        # Via=self.get_via_header()
        
        # _To=self.get_to_header()
        # Contact=self.get_Contact_header()
        _From=self.get_from_header()
        Call_ID=self.get_Call_ID_header()
        User_Agent=self.get_User_Agent_header()
        CLi=self.get_callerid()
        User_language=self.get_primary_language_header()
        if self.guest_language:
           Guest_Language_Code=self.guest_language['Rcode']
        else:
            Guest_Language_Code=self.get_guest_language_header()
        server=None
        if self.caller_info:
            id=self.caller_info['id']
            Name=self.caller_info['Name']
            CLi=self.caller_info['CLI']
            User_language=self.caller_info['primary_language']
            server=self.caller_info['SERVER']

        result = poly_db.add_record(self.starttime, Duration, Status,Name,id,CLi,_From,Call_ID,User_Agent,User_language,Guest_Language_Code,server)
        if result['status'] == True:
            agi.verbose('database %s' % result['string'])
        else:
            agi.verbose('database %s' % result['error_cause'])


    def update_call_guest_language(self,language):
        """Updates status of call"""
        
        result = poly_db.update_language(language)
        if result['status'] == True:
            agi.verbose('database %s' % result['string'])
        else:
            agi.verbose('database %s' % result['error_cause'])

    def update_call_status(self,status):
        """Updates status of call"""
        
        result = poly_db.update_status(status)
        if result['status'] == True:
            agi.verbose('database %s' % result['string'])
        else:
            agi.verbose('database %s' % result['error_cause'])

    def set_call_duration(self,duration):
        """Updates status of call"""
        
        result = poly_db.set_duration(duration)
        if result['status'] == True:
            agi.verbose('database %s' % result['string'])
        else:
            agi.verbose('database %s' % result['error_cause'])

    def store_poly_interaction(self):
        """Stores prompt played by the poly to the caller"""
        self.interaction_count += 1

        actor = 'poly'
        agi.verbose('[%d] bot -> caller: %s' %
                    (self.interaction_count, self.prompt))
        result = poly_db.add_utterance(
            self.interaction_count, self.status, self.prompt, actor, self.cause)
        if result['status'] == True:
            agi.verbose('database %s' % result['string'])
        else:
            agi.verbose('database %s' % result['error_cause'])

    def store_caller_interaction(self):
        """Stores caller's utterance returned by the gsr"""
        
        self.interaction_count += 1
        actor = 'caller'
        query_text = None
        if self.status == 'OK':
            if self.cause == '000':
                query_text = self.get_transcribed()
                agi.verbose('[%d] caller -> bot: %s' %
                            (self.interaction_count, query_text))
            else:
                agi.verbose('[%d] caller -> bot: completion cause [%s]' %
                            (self.interaction_count, self.cause))
        else:
            agi.verbose('[%d] caller -> bot: status [%s]' %
                        (self.interaction_count, self.status))
        result = poly_db.add_utterance(
            self.interaction_count, self.status, query_text, actor, self.cause)
        if result['status'] == True:
            agi.verbose('database %s' % result['string'])
        else:
            agi.verbose('database %s' % result['error_cause'])

    def LanguageSettingLoop(self):
        """Interacts with the caller in a loop until the dialog is complete"""
        self.store_starttime()
        self.get_caller_info()
        
        processing = True
        if self.action=="Unrecognized":
            agi.verbose("got prompt name  %s" % self.action)
            self.get_prompt(self.action)
            processing = False
        
        while processing:
            
            self.get_prompt(self.action)

            if self.action=="Confirmselection" :
                language_info=self.guest_language['Language']+","+self.guest_language['Dialect'] +"."
                self.prompt= self.prompt[:0]+ language_info +self.prompt

            if self.action=="Starttalking":
                processing=False
                self.ConversationLoop()

            self.transcribe_speech()
            processing = True
            if self.status == 'OK':
                if self.cause == '000':
                    self.language_selection()
                    self.set_call_duration(self.store_duration())
                    self.update_call_status(self.action)
                elif self.cause != '001' and self.cause != '002':
                    processing = False
            elif self.cause != '001' and self.cause != '002':
                processing = False

        self.store_poly_interaction()
        agi.appexec('MRCPSynth', "\\\"%s\\\"" % self.prompt)
        self.set_call_duration(self.store_duration())

    def ConversationLoop(self):
        """Interacts with the caller in a loop until the dialog is complete"""
        processing = True
        while processing:
            self.transcribe_speech()
            processing = True
            if self.status == 'OK':
                if self.cause == '000':
                    self.prompt = self.translate_prompt()
                    self.set_call_duration(self.store_duration())
                    self.update_call_status(self.action)
                elif self.cause != '001' and self.cause != '002':
                    processing = False
            elif self.cause != '001' and self.cause != '002':
                processing = False
        self.store_poly_interaction()
        agi.appexec('MRCPSynth', "\\\"%s\\\"" % self.prompt)
        self.set_call_duration(self.store_duration())

 


agi = AGI()

transcribe_app = SpeechTranscriptionApp()
poly_db = PolyDbConnector()
transcribe_app.LanguageSettingLoop()
    
agi.verbose('exiting')
# try:
#     transcribe_app = SpeechTranscriptionApp()
#     poly_db = PolyDbConnector()
#     transcribe_app.LanguageSettingLoop()
    
#     agi.verbose('exiting')
    

# except AGIHangup:
#     transcribe_app.set_call_duration(transcribe_app.store_duration())

