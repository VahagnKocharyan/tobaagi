#!/usr/bin/python3.6

from cmd import PROMPT
from pickle import TRUE
from subprocess import call
import sys
from telnetlib import STATUS
from xml.sax.handler import DTDHandler
import six
import os
from datetime import datetime,timezone,timedelta
from tokenize import Name
from tracemalloc import start
from typing import DefaultDict
from asterisk.agi import *
from translate import *
from tobadb import *
from config import *
from composedatetime import *
from sockettoba import *

"""current context"""
C='toba-in-two'
"""spy extension"""
S='spyonchannel'
"""called and callee channel extensions"""
cllc='called_channel'
cllce='callee_channel'

class SpeechTranscriptionApp:

    """A class representing speech transcription application"""

    def __init__(self):
        """Constructor"""
        self.options = None
        self.prompt = ""
        self.profile="2"
        self.single_utterance=None
        self.translation_status='on'
        self.action= "Selectlanguage_dtmf"
        self.interaction_count = 0
        self.status = None
        self.cause = None
        self.processing=True
        self.skip=False
        self.account=None
        self.primary_language=None
        self.guest_languages=None
        self.synthlanguage=None
        self.recoglanguage=None
        self.voice='en-US-Wavenet-C'
        self.calleeid=None
        os.environ[TRANSLATEKEYTYPE] = TRANSLATEKEYPATH
        
        


    def get_callerid(self):
        """Retrieves caller id from Asterisk"""

        agi.verbose('agi callerid %s' % agi.env['agi_callerid'])
        agi.verbose('asterisk callerid %s' % agi.get_variable('CALLERID(num)'))
        agi.verbose('asterisk callerid %s' % agi.get_variable('CALLERID(name)'))
        caller_id=agi.env['agi_callerid']
        if caller_id=='unknown':
            caller_id=agi.get_variable('callerid')
        numeric_filter = filter(str.isdigit, caller_id)
        numeric_string = "".join(numeric_filter)
        
        return numeric_string

    def get_calleeid(self):
        """Retrieves callee id from Asterisk"""
        agi.verbose('asterisk callee number %s' % agi.get_variable('calleeid'))
        return agi.get_variable('calleeid')

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

    def get_GLOBALID(self):
        """Retrieves to GLOBALID from Asterisk Sip invite request"""

        agi.verbose('GLOBALID header %s' % agi.get_variable('GLOBALID'))
        return agi.get_variable('GLOBALID')

    def get_User_Agent_header(self):
        """Retrieves User_Agent header from Asterisk Sip invite request"""

        agi.verbose('User-Agent header %s' % agi.get_variable('User_Agent'))
        return agi.get_variable('User_Agent')
    
    def get_primary_language_header(self):
        """Retrieves x-primary-language header from Asterisk Sip invite request"""

        agi.verbose('x-primary-language %s' % agi.get_variable("Primary_language"))
        return agi.get_variable("Primary_language")

    def get_guest_language_from_asterisk(self):
        """Retrieves guest language from asterisk"""

        agi.verbose('got guest language from asterisk %s' % agi.get_variable("guestlanguage"))
        return agi.get_variable("guestlanguage")

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

        self.store_toba_interaction()
        if self.action=='Starttalking' :
            self.synth()
            self.recog()
            
        else:
            self.synth_and_recog()
        self.store_caller_interaction()

    def synth(self):
        agi.appexec('MRCPSynth', "\\\"%s\\\",l=%s&v=%s&p=2" % (self.prompt,self.synthlanguage['Rcode'],self.synthlanguage['Scode']))

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

        if self.guest_languages:
            grammar = self.append_grammar_parameter(
                grammar, "alternate-languages", self.guest_languages['Rcode'], separator)
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

    def compose_speech_options(self):
        """Composes speech options"""
        options=toba_db.get_timeouts()
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
                defauloptions, "dit", '5000', separator)

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

        if self.primary_language:
            agi.verbose('set grammar primary language to  %s' % self.primary_language)
            options = self.append_option_parameter(
                options, "spl",self.primary_language['Rcode'], separator)

            options = self.append_option_parameter(
                options, "vn", self.primary_language['Scode'], separator)
            
        if self.profile:
            options = self.append_option_parameter(
                options, "p", self.profile, separator)
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
        if language_code=="ar-x-gulf":
            language_code='ar-XA'
        if language_code=="cmn-hant-tw":
            language_code='zh-tw'
        
        agi.verbose('got transcribtion language_code %s' % language_code)

        return language_code

    def get_caller_account(self):
        """Get caller account info from mongodb"""
        result= toba_db.get_caller_info(self.get_callerid())
        # agi.verbose(result)
        if result['status'] == True:
            accountfullname=result['account']['name']['full']
            guestlangauges=result['account']['languages']['guest']
            primarylangauges=result['account']['languages']['primary']
            agi.verbose('database -> current user: %s ,account primary language: %s ,current guest languages: %s' % (accountfullname,primarylangauges,guestlangauges))
            self.account=result['account']
        else:
            agi.verbose('database -> failed to get caller info:%s' % result['error_cause'])
    
    def set_toba_primary_language(self):
        """Get primary  language object from account object"""
        if self.account:
            self.primary_language=self.account['languages']['primary'][0]
        else:
            self.primary_language=dict({'Rcode':'en-US'})
        agi.verbose('current primary language %s' % self.primary_language)

    def set_toba_guest_languages(self):
        """Get guest languega object from account object"""
        if self.account:
            self.guest_languages=self.account['languages']['guest']
        agi.verbose('current guest languages %s' % self.guest_languages)

    def set_callie_number(self):
        """set callee number"""
        self.calleeid=self.get_calleeid()

    def get_prompts(self):
        """Get prompt from account object"""
        prompt=""
        if self.account:
            agi.verbose('got current account prompts %s' % self.account['Prompts'])
            prompt+= self.account['Prompts'][self.action]

            if self.action=='translation_status':
                prompt=" " + prompt.format(self.guest_languages['Language'],self.translation_status)

            if self.action=='Wrongselection':
                prompt=" " + prompt.format(len(self.guest_languages))

            if self.action=='Selectlanguage_dtmf':
                for k in self.guest_languages:
                    agi.verbose('got key info->%s'%k)
                    prompt+=" " + str(self.account['Prompts']['dtmf_prompt']).format(k['Language'],self.guest_languages.index(k)+1)
            
        else:
            """Get prompt direct from mongodb"""
            result= toba_db.get_prompts(self.action)
            if result['status'] == True: 
                
                self.prompt= result['PROMPTTEXT']
            else:
                agi.verbose('database -> failed to get caller info:%s' % result['error_cause'])

        

            
        self.prompt=prompt
        agi.verbose('got current prompt %s' % self.prompt)

    def set_toba_action(self):
        self.get_caller_account()
        self.set_toba_primary_language()
        self.set_callie_number()
        if not self.account:
            self.action='Unrecognized'

        self.set_toba_guest_languages()
        if self.guest_languages and len(self.guest_languages)==1 :
            self.guest_languages=self.guest_languages[0]
            self.update_call_guest_language(self.guest_languages['Rcode'])
            agi.verbose('current alternative languages from acoount %s' % self.guest_languages)
            self.action="Starttalking"
            self.synthlanguage=self.primary_language
            self.skip=True

        if not self.guest_languages:
            self.action="Guestlanguagenotselected"

        if self.get_GLOBALID():
            guest_language=self.account['lastcalllogs']['SelectedGuestLanguageCode']
            if guest_language:
                for k in self.guest_languages:
                        agi.verbose('got key info->%s'%k)
                        if k['Rcode']==guest_language:
                            self.guest_languages=k
                            self.action="Starttalking"
                            self.synthlanguage=self.primary_language
                            self.skip=True
                            break
        # primary_language_header=self.get_primary_language_header()
        # guest_language_header = self.get_guest_language_header()
        # if primary_language_header!="" and guest_language_header!="" :
               
        #        self.primary_language=primary_language_header
        #        self.alternative_languages=guest_language_header
        #        self.action="Starttalking"
        #        self.skip=True

        self.synthlanguage=self.primary_language
        self.add_db_record()
            



    def get_translation(self,text,Tcode):
        from google.cloud import translate_v2 as translate
        import six
        result=None
        if isinstance(text, six.binary_type):
            text = text.decode("utf-8")
        try:
            translate_client = translate.Client()
            agi.verbose('%s -> translate to  guest -> %s' %(text,Tcode))
            results = translate_client.translate(text, target_language=Tcode)
            agi.verbose('got google translate result  %s' %results)
        except Exception as e:
            agi.verbose('got google translate error   %s' %e)
        result=results["translatedText"].replace('&#39;',"'") 
        agi.verbose('got google detectedSourceLanguage   %s' %results["detectedSourceLanguage"])
        return  result


    def translate_prompt(self):
        prompt= ""
        transcribed=self.get_transcribed()
        if self.get_language_code()==self.guest_languages['Rcode'].lower() :
            agi.verbose('%s -> translate to primary language-> %s' %(transcribed,self.primary_language['Tcode']))
            self.synthlanguage=self.primary_language
            prompt=self.get_translation(str(transcribed),self.primary_language['Tcode'])

        if self.get_language_code()==self.primary_language['Rcode'].lower() :
            agi.verbose('%s -> translate to  guest -> %s' %(transcribed,self.guest_languages['Tcode']))
            self.synthlanguage=self.guest_languages
            prompt=self.get_translation(str(transcribed),self.guest_languages['Tcode']) 

        agi.verbose('%s -> %s' %(transcribed,prompt))
        return prompt

    def store_toba_interaction(self):
        """Stores prompt played by the toba to the caller"""
        self.interaction_count += 1

        actor = 'toba'
        agi.verbose('[%d] bot -> caller: %s' %
                    (self.interaction_count, self.prompt))
        utterances={
            'UtteranceIndex':self.interaction_count,
            'UpdatedTimestamp':str(self.starttime),
            'UtteranceStatus':self.status,
            'UtteranceText':self.prompt if self.cause!='002' else 'waiting',
            'UtteranceActor':actor,
            'UtteranceCause':self.cause,
        }
        result = toba_db.add_utterance(utterances)
        if result['status'] == True:
            agi.verbose('database %s-->%s' % (result['string'],result['record_id']))
            socketapp.updateutterances(str(result['record_id']))
        else:
            agi.verbose('database %s' % result['error_cause'])

        

    def store_caller_interaction(self):
        """Stores caller's utterance returned by the gsr"""
        
        self.interaction_count += 1
        actor = agi.get_variable("SPYCHANNEL"),
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
        utterances={
            'UtteranceIndex':self.interaction_count,
            'UpdatedTimestamp':str(self.starttime),
            'UtteranceStatus':self.status,
            'UtteranceText':query_text if self.cause!='002' else 'waiting',
            'UtteranceActor':actor,
            'UtteranceCause':self.cause,
        }
        result = toba_db.add_utterance(utterances)
        if result['status'] == True:
            agi.verbose('database %s' % result['string'])
            socketapp.updateutterances(str(result['record_id']))
        else:
            agi.verbose('database %s' % result['error_cause'])




    def language_selection(self):
        agi.verbose('current prompt name -> %s' % self.action)
        
        if self.action=="Selectlanguage_dtmf" or self.action=="Wrongselection" :
            dtmf=self.get_dtmf() 
            if dtmf:
                key=int(dtmf)-1
                if key<len(self.guest_languages):
                    self.action="Selectnumber_dtmf"      
                    agi.verbose('selected language %s' % self.guest_languages )
                    self.guest_languages=self.guest_languages[key]
                    self.update_call_guest_language(self.guest_languages['Rcode'])
                else:
                    self.action="Wrongselection"
    
    def number_selection1(self):
        if self.action=='Selectnumber_dtmf':
            self.get_prompts()
            dtmf=self.get_dtmf() 

            if dtmf and len(dtmf)>1:
                agi.set_variable('CALLERID(num)', '%s' %self.get_callerid())
                agi.set_variable('CALLERID(name)','toba' )
                agi.appexec('DIAL','SIP/%s)'%dtmf)
                agi.appexec('originate','agi(tobamongo/tobalast.py),app,Chanspy,",Bd(SIP/%s)Eoqw",,,av(SPYCHANNEL=CALLER^GLOBALID=${SIP_HEADER(Call-ID)})c' % dtmf)

                # agi.appexec('originate','local/786@from-phone1,app,Chanspy,",Bd(SIP/%s)Eoqw",,,av(SPYCHANNEL=CALLER^GLOBALID=${SIP_HEADER(Call-ID)})c' % dtmf)
                # agi.appexec('originate','local/786@from-phone1,app,Chanspy,",Bd(SIP/%s)Eoqw",,,v(SPYCHANNEL=CALLER^GLOBALID=${SIP_HEADER(Call-ID)})c' % self.get_callerid())
                self.action='Stoptalking'
    # def setspygoups(self):

    def number_selection(self):
        if self.action=='Selectnumber_dtmf':
            self.get_prompts()
            dtmf=self.get_dtmf() 

            if dtmf and len(dtmf)>1:
                agi.set_variable('CALLERID(num)', '%s' %self.get_callerid())
                agi.set_variable('CALLERID(name)','toba' )
                agi.set_variable('number','%s' %dtmf)
                agi.set_variable('primarylanguage','%s' %self.primary_language['Rcode'])
                agi.set_variable('guestlanguage','%s' %self.guest_languages['Rcode'])
                # agi.set_variable('OPTIONScllc',",bBg(CALLER)Eqow")
                # agi.set_variable('OPTIONScllce',",bBg(CALLEE)Eqow")
                # exten => s,2,Dial(PJSIP/${ARG1}@VoiceConnector,20,b(uniastspy^called_channel^1(AGENT))B(uniastspy^callee_channel^1(CALLER))tU(originate__spy^${CHANNEL(pjsip,call-id)},${CALLERID(num)},${CALLERID(dnid)}))
                agi.appexec('dial',f'SIP/{dtmf}@441651,20,b({C}^{cllce}^1(CALLEE))B({C}^{cllc}^1(CALLER))tU({S}^{self.get_Call_ID_header()}^{self.get_callerid()}^{dtmf})')
                # agi.appexec('originate','agi(tobamongo/tobalast.py),app,Chanspy,",Bd(SIP/%s)Eoqw",,,av(SPYCHANNEL=CALLER^GLOBALID=${SIP_HEADER(Call-ID)})c' % dtmf)

                # agi.appexec('originate','local/%s@clickincontext,exten,,,,,v(SPYCHANNEL=CALLER^GLOBALID=${SIP_HEADER(Call-ID)})c '%dtmf)
                # agi.appexec('originate','local/786@from-phone1,app,Chanspy,",Bd(SIP/%s)Eoqw",,,av(SPYCHANNEL=CALLER^GLOBALID=${SIP_HEADER(Call-ID)})c' % dtmf)
                self.action='Stoptalking'

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
        calllogsGLOBALID=self.get_GLOBALID()
        calllogs = { 
                'AccountId':self.account['_id'] if self.account else 'not registered' ,
                'CallID':self.get_Call_ID_header() if agi.get_variable('Call_ID') else calllogsGLOBALID,
                'UserCLI':self.account['phone'] if self.account else self.get_callerid(),
                'StartTime':self.starttime,
                'Duration':'Duration',
                'Status':self.action,
                'From':self.get_from_header(),
                'UserAgent':self.get_User_Agent_header(),
                'PrimaryLanguage':self.primary_language['Rcode'] if self.account else self.get_primary_language_header(),
                'SelectedGuestLanguageCode':str(self.guest_languages) if self.account  else self.get_guest_language_header(),
                'ServerCountry': self.account['server'] if self.account else 'not registered' 
             }
        agi.verbose('data to insert to calllogs collection %s' % calllogs)
        result = toba_db.add_record(calllogs,calllogsGLOBALID)
        if result['status'] == True:
            agi.verbose('database %s' % result['string'])
        else:
            agi.verbose('database %s' % result['error_cause'])


    def update_call_guest_language(self,language):
        """Updates status of call"""
        
        result = toba_db.update_language(language)
        if result['status'] == True:
            agi.verbose('database %s' % result['string'])
        else:
            agi.verbose('database %s' % result['error_cause'])

    def update_call_status(self,status):
        """Updates status of call"""
        
        result = toba_db.update_status(status)
        if result['status'] == True:
            agi.verbose('database %s' % result['string'])
        else:
            agi.verbose('database %s' % result['error_cause'])

    def set_call_duration(self,duration):
        """Updates status of call"""
        
        result = toba_db.set_duration(duration)
        if result['status'] == True:
            agi.verbose('database %s' % result['string'])
        else:
            agi.verbose('database %s' % result['error_cause'])

    def LanguageSettingLoop(self):
        """Interacts with the caller in a loop until the dialog is complete"""
        
        self.store_starttime()
        self.get_caller_account()
        self.set_toba_action()
        self.set_call_duration(self.store_duration())
        self.update_call_status(self.action)
        socketapp.connect()
        socketapp.register()
        self.processing = True
        if self.action=="Unrecognized" or self.action=="Guestlanguagenotselected":
            agi.verbose("got prompt name  %s" % self.action)
            self.get_prompts()
            self.processing = False

        

        while self.processing:
            agi.verbose("got prompt name  %s" % self.action)
            self.get_prompts()
            

            if self.action=="Starttalking" and self.translation_status=='on':
                self.processing=False
                self.ConversationLoop()
                self.wait()

            if self.action=='Stoptalking':
                self.processing=False
                self.get_prompts()
                agi.verbose("got processing %s" % self.processing)
                break
            self.transcribe_speech()
            # self.processing = True
            if self.status == 'OK':
                if self.cause == '000':
                    self.language_selection()
                    self.number_selection()
                    self.set_call_duration(self.store_duration())
                    self.update_call_status(self.action)
                    
                elif self.cause != '001' and self.cause != '002':
                    self.processing = False
            elif self.cause != '001' and self.cause != '002':
                self.processing = False
        self.set_call_duration(self.store_duration())
        agi.verbose("ugyhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
        self.synth()

    def wait(self):

        self.processing = True
        self.compose_speech_options()
        agi.verbose('current primary language voice name  %s user language %s'%(self.primary_language['Scode'],self.primary_language['Rcode']))
        self.synth()
        while self.processing:
            dtmf=agi.wait_for_digit(timeout=2000)
            agi.verbose("got dtmf %s"%dtmf)
            if dtmf=='0':
                self.translation_status=self.getoposit()
                self.action='translation_status'
                self.get_prompts()
                self.synth()
                self.action="Starttalking"
                self.get_prompts()
                self.ConversationLoop()

    def ConversationLoop(self):
        """Interacts with the caller in a loop until the dialog is complete"""
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
                            self.action='translation_status'
                            self.get_prompts()
                            if self.translation_status=='off':
                                self.wait()
                        
                    self.set_call_duration(self.store_duration())
                    self.update_call_status(self.action)
                elif self.cause=='002':
                    self.prompt=' '
                elif self.cause != '001' and self.cause != '002':
                    self.processing = False
            elif self.cause != '001' and self.cause != '002':
                self.processing = False

        
        self.set_call_duration(self.store_duration())
        
 


agi = AGI()


transcribe_app = SpeechTranscriptionApp()
toba_db = TobaDbConnector()
socketapp=SocketToba(transcribe_app.get_callerid())
"""to replace or register a method in the other class"""
def new_test_hangup():
    if agi._got_sighup:
        socketapp.disconnectt()
        # agi.hangup()
        
agi.test_hangup = new_test_hangup

transcribe_app.LanguageSettingLoop()
socketapp.disconnectt()
agi.verbose('exiting')