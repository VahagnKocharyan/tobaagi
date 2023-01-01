#!/usr/bin/python3
"""
    Asterisk AGI custom application 

    This script interacts with gsr and gss API via UniMRCP server.

    * Revision: 1
    * Date: dec 29, 2021
    * Vendor: Vahagn kocharyan kocharyan.vahagn@gmail.com
"""
import sys
from asterisk.agi import *
from translate import *
from polydb import *
from config import *
import six
import os


class SpeechTranscriptionApp:

    """A class representing speech transcription application"""

    def __init__(self):
        """Constructor"""
        self.options = None
        self.prompt = ""
        self.language = None
        self.guest_language=None
        self.alternative_languages = None
        self.lang_confirmation=False
        self.action= "Selectlanguage"
        self.status = None
        self.cause = None
        os.environ[TRANSLATEKEYTYPE] = TRANSLATEKEYPATH


    def get_callerid(self):
        """Retrieves caller id from Asterisk"""

        #agi.verbose('callerid %s' % agi.env['agi_callerid'])
        callerid=agi.get_variable('CALLER_ID')
        return callerid



    def transcribe_speech(self):
        """Performs a streaming speech transcription"""
        self.options=self.compose_speech_options()
        if self.action=="Starttalking" or self.action=="translation":
            self.grammars = "%s,%s" % (self.compose_speech_grammar(), self.compose_dtmf_grammar())
        else:
            
            self.grammars = "%s" % (self.compose_dtmf_grammar())

        self.synth_and_recog()

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
        
    def compose_speech_options(self):
        """Composes speech options"""

        if self.action=="Starttalking":
            options = 'plt=1&b=1&sct=1500&sint=15000&nit=10000'
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
            self.language=self.get_language_info_from_db(self.caller_info['primary_language'])          

        else:
            agi.verbose('database -> failed to get caller info:%s' % caller_info['error_cause'])
            self.action =caller_info['error_cause']
            self.language=dict()
            self.language['Tcode']='en' 
            


            
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
                            
                else:
                    
                    language_info=self.get_language_info_from_db(language_code)
                    self.guest_language=language_info
   
            else:
                self.lang_confirmation=False
                self.action="Wrongselection"


         



    def LanguageSettingLoop(self):
        """Interacts with the caller in a loop until the dialog is complete"""
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
                elif self.cause != '001' and self.cause != '002':
                    processing = False
            elif self.cause != '001' and self.cause != '002':
                processing = False
        agi.appexec('MRCPSynth', "\\\"%s\\\"" % self.prompt)

    def ConversationLoop(self):
        """Interacts with the caller in a loop until the dialog is complete"""
        processing = True
        while processing:
            self.transcribe_speech()
            processing = True
            if self.status == 'OK':
                if self.cause == '000':
                    self.prompt = self.translate_prompt()
                elif self.cause != '001' and self.cause != '002':
                    processing = False
            elif self.cause != '001' and self.cause != '002':
                processing = False

        agi.appexec('MRCPSynth', "\\\"%s\\\"" % self.prompt)


agi = AGI()

transcribe_app = SpeechTranscriptionApp()
poly_db = PolyDbConnector()
transcribe_app.LanguageSettingLoop()
agi.verbose('exiting')
