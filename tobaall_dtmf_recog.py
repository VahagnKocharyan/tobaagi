#!/usr/bin/python3
"""
    Asterisk TEST AGI custom application 

    This script interacts with gsr and gss API via UniMRCP server.

    * Revision: 4
    * Date: jun 1, 2022
    * Vendor: Vahagn kocharyan kocharyan.vahagn@gmail.com
"""
from cmd import PROMPT
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
        self.user_language=None
        self.guest_language=None
        self.caller_info= None
        self.single_utterance=None
        self.alternative_languages = None
        self.translation_status='on'
        self.action= "Selectlanguage_dtmf"
        self.interaction_count = 0
        self.status = None
        self.cause = None
        self.processing=True
        self.brandprompt=None
        self.skip=False
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
            self.grammars = "%s,%s" % (self.compose_speech_grammar(),self.compose_dtmf_grammar())
        else:
            
            self.grammars = "%s" % (self.compose_dtmf_grammar())

        self.store_poly_interaction()
        if self.action=='Starttalking':
            self.synth()
            self.recog()
        else:
            self.synth_and_recog()
        self.store_caller_interaction()

    def synth(self):
        agi.appexec('MRCPSynth', "\\\"%s\\\",l=%s&v=%s" % (self.prompt,self.syntlanguage['Rcode'],self.syntlanguage['Scode']))

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


    def recog(self):
        """This is an internal function which calls MRCPRecog"""
        self.grammars = "%s,%s" % (self.compose_speech_grammar(), self.compose_dtmf_grammar())
        args = "\\\"%s\\\",%s" % (self.grammars, self.options)
        agi.appexec('MRCPRecog', args)
        self.status = agi.get_variable('RECOGSTATUS') 
        # agi.verbose('got status %s' % self.status)
        if self.status == 'OK':
            self.cause = agi.get_variable('RECOG_COMPLETION_CAUSE')
            # agi.verbose('got completion cause %s' % self.cause)
        else:
            agi.verbose('Recognition completed abnormally')
        self.cause = agi.get_variable('RECOG_COMPLETION_CAUSE')



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
                options, "vn", self.language['Scode'], separator)
            
            
        return options
        



    def get_transcribed(self):
        """get transcription"""

        transcription=agi.get_variable('RECOG_INSTANCE(0/0/StreamingRecognitionResult/alternatives/transcript)')
        agi.verbose('got transcription %s' % transcription)

        return transcription

    def getoposit(self):
        agi.verbose('got translation status %s' % self.translation_status)
        status=self.translation_status
        if status=='on':
            status='off'
        else:
            status='on'
        return status


    def get_dtmf(self):
        """get dtmf"""
        DTMF=None
        dtmf=str(agi.get_variable('RECOG_INSTANCE(0/0)'))
        # # if dtmf.isnumeric():
        # if isinstance(dtmf, str):
        #     dtmf = unicode(dtmf, 'utf-8')

        isnumeric=dtmf.isnumeric()
        agi.verbose('got dtmf is numeric %s' % isnumeric)
        if type(isnumeric) == type(True):
            DTMF=dtmf

        return dtmf

    def get_language_code(self):
        """get language code"""

        language_code=agi.get_variable('RECOG_INSTANCE(0/0/StreamingRecognitionResult/language_code)')
        if language_code=="cmn-hant-tw":
            language_code='zh-tw'
        
        agi.verbose('got transcribtion language_code %s' % language_code)

        return language_code


    def get_brandprompt(self):
        prompt_info = poly_db.get_prompt_info("Selectlanguage_dtmf")
        if prompt_info['status'] == True: 
            self.brandprompt= self.get_translation(prompt_info['PROMPTTEXT'],str(self.language['Tcode']))
        else:
           agi.verbose('database %s' % prompt_info['error_cause'])

        


    def get_prompt(self,action):
        agi.verbose('i am heeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
        
        prompt_info = poly_db.get_prompt_info(action)

        if prompt_info['status'] == True: 
            prompt=prompt_info['PROMPTTEXT']
            dtmfprompt=poly_db.get_prompt_info('dtmf_prompt')
            if action=='translation_status':
                agi.verbose('line 280')
                prompt=str(prompt).format(self.guest_language['Language'],self.translation_status)

            if dtmfprompt['status'] and action=='Selectlanguage_dtmf':
                for k in self.caller_info['guest_languages']:
                    agi.verbose('got key info->%s'%k)
                    guest_language=self.get_language_info_from_db(self.caller_info['guest_languages'][k])
                    agi.verbose('got caller info->%s'%guest_language['Language'])
                    # pompttext=dtmfprompt['PROMPTTEXT']
                    prompt+=" " + str(dtmfprompt['PROMPTTEXT']).format(guest_language['Language'],k.replace('R',''))
            
            # if self.action=="Starttalking":
            #     prompt=prompt[:0]+prompt

                
            self.prompt=self.get_translation(prompt,str(self.language['Tcode']))
            agi.verbose('got prompt info->%s'%self.prompt)

        
        # if prompt_info['status'] == True:
        #     agi.verbose('database -> got prompt info%s' % prompt_info)
        #     agi.verbose('got language->%s'%self.language['Tcode'])
        #     agi.verbose('got caller info->%s'%self.alternative_languages)
        #     self.prompt=self.get_translation(prompt_info['PROMPTTEXT'],str(self.language['Tcode'])) 
            
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
                self.skip=True

            primary_language_header=self.get_primary_language_header()
            guest_language_header = self.get_guest_language_header()
            if primary_language_header!="" and guest_language_header!="" :
               
               self.caller_info['primary_language']=primary_language_header
               self.alternative_languages=self.guest_language=self.get_language_info_from_db(guest_language_header)
               self.action="Starttalking"
               self.skip=True
            

            self.language=self.get_language_info_from_db(self.caller_info['primary_language']) 
            self.user_language=self.language  
            self.syntlanguage=self.language       
            self.get_brandprompt()
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

    



    def get_translation(self,text,Tcode):
        """Detects the text's language."""
        from google.cloud import translate_v2 as translate
        import six
        if isinstance(text, six.binary_type):
            text = text.decode("utf-8")
        try:
            translate_client = translate.Client()
            result = translate_client.translate(text, target_language=Tcode)
            agi.verbose('got google translate result  %s' %result)
        except Exception as e:
            agi.verbose('got google translate error   %s' %e)

        return result["translatedText"].replace('&#39;',"'")       
       

    def translate_prompt_earlier(self):
        prompt= ""
        
        primary_language=self.get_language_info_from_db(self.caller_info['primary_language'])
        guest_language=self.guest_language
        transcribed=self.get_transcribed()
        if self.get_language_code()==guest_language['Rcode'].lower() and self.get_language_code()!=self.language:
            agi.verbose('%s -> translate to guest language-> %s' %(transcribed,primary_language['Tcode']))
            prompt=self.get_translation(str(transcribed),primary_language['Tcode'])
            self.language=primary_language
            self.alternative_languages=guest_language

        if self.get_language_code()==primary_language['Rcode'].lower() and self.get_language_code()!=self.language:
            agi.verbose('%s -> translate to  primary -> %s' %(transcribed,guest_language['Tcode']))
            prompt=self.get_translation(str(transcribed),guest_language['Tcode']) 
            self.language=guest_language
            
            self.alternative_languages=primary_language

        agi.verbose('current options->%s'% self.options)
        agi.verbose('current language : %s' %(self.language))
        agi.verbose('%s -> %s' %(transcribed,prompt))
        return prompt

    def translate_prompt(self):
        prompt= ""
        
        primary_language=self.get_language_info_from_db(self.caller_info['primary_language'])
        guest_language=self.guest_language
        transcribed=self.get_transcribed()
        if self.get_language_code()==guest_language['Rcode'].lower() and self.get_language_code()!=self.language:
            agi.verbose('%s -> translate to guest language-> %s' %(transcribed,primary_language['Tcode']))
            prompt=self.get_translation(str(transcribed),primary_language['Tcode'])
            self.syntlanguage=primary_language
            # self.language=primary_language
            # self.alternative_languages=guest_language

        if self.get_language_code()==primary_language['Rcode'].lower() and self.get_language_code()!=self.language:
            agi.verbose('%s -> translate to  primary -> %s' %(transcribed,guest_language['Tcode']))
            prompt=self.get_translation(str(transcribed),guest_language['Tcode']) 
            self.syntlanguage=guest_language
            # self.language=guest_language
            
            # self.alternative_languages=primary_language

        agi.verbose('current options->%s'% self.options)
        agi.verbose('current language : %s' %(self.language))
        agi.verbose('%s -> %s' %(transcribed,prompt))
        return prompt

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
                if self.action=='Selectlanguage_dtmf' or self.action=='Wrongselection':
                    query_text=self.get_dtmf()
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




    def language_selection(self):
        agi.verbose('current prompt name -> %s' % self.action)
        
        if self.action=="Selectlanguage_dtmf" or self.action=="Wrongselection" :
            dtmf=self.get_dtmf() 
            if dtmf:
                key='R%s'%dtmf
                if key in self.caller_info['guest_languages']:
                    language_code=self.caller_info['guest_languages'][key] 
                    self.action="Starttalking"      
                    
                    if not self.guest_language:
                        agi.verbose('selected language %s' % self.guest_language )
                        language_info=self.get_language_info_from_db(language_code)
                        self.guest_language=language_info

                    agi.verbose('selected language %s' % self.guest_language )

                    self.alternative_languages=self.guest_language
                    self.update_call_guest_language(self.guest_language['Rcode'])
    
                else:
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

    def LanguageSettingLoop(self):
        """Interacts with the caller in a loop until the dialog is complete"""
        self.store_starttime()
        self.get_caller_info()
        
        # self.processing = True
        if self.action=="Unrecognized":
            agi.verbose("got prompt name  %s" % self.action)
            self.get_prompt(self.action)
            self.processing = False
        
        while self.processing:
            
            self.get_prompt(self.action)

            

            if self.action=="Starttalking" and self.translation_status=='on':
                # self.processing=False
                self.ConversationLoop()
                self.wait()
                
            self.transcribe_speech()
            # self.processing = True
            if self.status == 'OK':
                if self.cause == '000':
                    self.language_selection()
                    self.set_call_duration(self.store_duration())
                    self.update_call_status(self.action)
                elif self.cause != '001' and self.cause != '002':
                    self.processing = False
            elif self.cause != '001' and self.cause != '002':
                self.processing = False
        # agi.appexec('MRCPSynth', "\\\"%s\\\"" % self.prompt)
        self.set_call_duration(self.store_duration())


    def wait(self):
        self.processing = True
        
        self.compose_speech_options()
        agi.verbose('current user language name  %s user language %s'%(self.user_language['Scode'],self.user_language['Rcode']))
        agi.appexec('MRCPSynth', "\\\"%s\\\",\\\"v=%s&l=%s\\\"" % (self.prompt,self.user_language['Scode'],self.user_language['Rcode']))
        
        while self.processing:
            dtmf=agi.wait_for_digit(timeout=2000)
            agi.verbose("got dtmf %s"%dtmf)
            if dtmf=='0':
                self.translation_status=self.getoposit()
                self.get_prompt("translation_status")
                self.ConversationLoop()

    def ConversationLoop(self):
        """Interacts with the caller in a loop until the dialog is complete"""
        if self.brandprompt and self.skip:    
           self.prompt= self.prompt[:0]+ self.brandprompt +self.prompt
        self.processing = True
        while self.processing:
            self.transcribe_speech()
            
            if self.status == 'OK':
                if self.cause == '000':
                    

                    self.prompt = self.translate_prompt()
                    if not self.prompt:
                        dtmf=self.get_dtmf()
                        if dtmf and dtmf=='0':
                            self.translation_status=self.getoposit()
                            self.alternative_languages=self.language
                            self.language=self.user_language
                            self.get_prompt("translation_status")
                            if self.translation_status=='off':
                                self.wait()
                        
                    self.set_call_duration(self.store_duration())
                    self.update_call_status(self.action)
                elif self.cause != '001' and self.cause != '002':
                    self.processing = False
            elif self.cause != '001' and self.cause != '002':
                self.processing = False

        
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

