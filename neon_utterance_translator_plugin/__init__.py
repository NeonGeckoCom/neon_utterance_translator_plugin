# # NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# # All trademark and other rights reserved by their respective owners
# # Copyright 2008-2021 Neongecko.com Inc.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from ovos_plugin_manager.language import OVOSLangDetectionFactory, OVOSLangTranslationFactory
from ovos_utils.log import LOG

from neon_transformers import UtteranceTransformer
from neon_transformers.tasks import UtteranceTask
from neon_utils.configuration_utils import get_neon_lang_config

class UtteranceTranslator(UtteranceTransformer):
    task = UtteranceTask.TRANSLATION

    def __init__(self, name="utterance_translator", priority=5):
        super().__init__(name, priority)
        self.language_config = get_neon_lang_config()
        self.supported_langs = self.language_config['language'].get('intents') or [
            self.language_config['language'].get("internal") or "en-us"]
        self.lang_detector = OVOSLangDetectionFactory.create()
        self.translator = OVOSLangTranslationFactory.create()

    def transform(self, utterances, context=None):
        metadata = []
        lang = context.get('lang') or 'en-us'

        for idx, ut in enumerate(utterances):
            try:
                original = ut
                detected_lang = self.lang_detector.detect(original)
                if detected_lang != lang.split('-', 1)[0]:
                    LOG.warning(f"Specified lang: {lang} but detected {detected_lang}")
                else:
                    LOG.debug(f"Detected language: {detected_lang}")
                if detected_lang not in self.supported_langs:
                    utterances[idx] = self.translator.translate(
                        original,
                        self.language_config["internal"],
                        detected_lang)
                    LOG.info(f"Translated utterance to: {utterances[idx]}")
                # add language metadata to context
                metadata += [{
                    "source_lang": lang,
                    "detected_lang": detected_lang,
                    "internal": self.language_config["internal"],
                    "was_translated": lang.split('-', 1)[0] != detected_lang,
                    "raw_utterance": original
                }]
            except Exception as e:
                LOG.error(e)
        # return translated utterances + data
        return utterances, {"translation_data": metadata}
