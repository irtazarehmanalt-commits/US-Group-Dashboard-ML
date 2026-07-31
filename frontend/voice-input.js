// Speech-to-text for the chatbot, via the browser's built-in Web Speech API
// (SpeechRecognition). Loaded as a plain <script> in index.html - BEFORE
// app.js's fetch+Babel step - so it's plain, un-transpiled JS with no JSX and
// no React dependency. It just exposes one global, window.VoiceInput, which
// app.js's React components call into; this file has no idea a chat UI even
// exists.
//
// Browser support: Chrome/Edge expose this as the vendor-prefixed
// `webkitSpeechRecognition`; Firefox has no implementation at all; Safari's
// support is partial and inconsistent. VoiceInput.isSupported() lets the UI
// hide the mic button entirely where it won't work, instead of showing a
// button that fails.
(function () {
  var SpeechRecognitionImpl = window.SpeechRecognition || window.webkitSpeechRecognition;

  var recognition = null;
  var listening = false;

  function isSupported() {
    return !!SpeechRecognitionImpl;
  }

  function isListening() {
    return listening;
  }

  // callbacks: { onResult(transcript, isFinal), onError(errorCode), onEnd() }
  // onResult fires repeatedly while the user talks (interim results) and once
  // more with isFinal=true - the caller decides what to do with each update
  // (this feature just keeps overwriting the chat input with the latest
  // transcript, so the user sees their words appear live).
  function start(callbacks) {
    callbacks = callbacks || {};
    if (!isSupported() || listening) return;

    recognition = new SpeechRecognitionImpl();
    recognition.lang = 'en-US';
    recognition.continuous = false; // one utterance per mic press, not an open mic
    recognition.interimResults = true; // stream partial text while still speaking

    recognition.onresult = function (event) {
      var transcript = '';
      var isFinal = false;
      for (var i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
        if (event.results[i].isFinal) isFinal = true;
      }
      if (callbacks.onResult) callbacks.onResult(transcript.trim(), isFinal);
    };

    // e.g. 'not-allowed' (mic permission denied), 'no-speech', 'network'
    recognition.onerror = function (event) {
      listening = false;
      if (callbacks.onError) callbacks.onError(event.error);
    };

    recognition.onend = function () {
      listening = false;
      if (callbacks.onEnd) callbacks.onEnd();
    };

    listening = true;
    recognition.start();
  }

  function stop() {
    if (recognition && listening) recognition.stop();
  }

  window.VoiceInput = {
    isSupported: isSupported,
    isListening: isListening,
    start: start,
    stop: stop,
  };
})();
