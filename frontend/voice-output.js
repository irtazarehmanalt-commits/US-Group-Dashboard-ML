// Text-to-speech for the chatbot's answers, via the browser's built-in Web
// Speech API (SpeechSynthesis). Same plain-<script> pattern as voice-input.js
// - exposes window.VoiceOutput, no React/JSX, no knowledge of the chat UI.
//
// Browser support is much wider than SpeechRecognition (Chrome, Edge,
// Safari, Firefox all implement SpeechSynthesis), so this one doesn't bother
// with a "hide the button" isSupported() gate in the UI, but the function is
// still provided for consistency and for the rare browser with neither.
(function () {
  function isSupported() {
    return !!window.speechSynthesis;
  }

  // opts: { rate, pitch, lang, onEnd(), onError() }
  function speak(text, opts) {
    if (!isSupported() || !text) return;
    opts = opts || {};

    // Cancel whatever's currently speaking first - without this, clicking
    // "Listen" on a second answer would queue behind the first instead of
    // replacing it, which reads as the app being stuck.
    window.speechSynthesis.cancel();

    var utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = opts.rate || 1;
    utterance.pitch = opts.pitch || 1;
    utterance.lang = opts.lang || 'en-US';
    if (opts.onEnd) utterance.onend = opts.onEnd;
    // cancel() above fires 'error' (not 'end') on whatever utterance it
    // interrupted, so callers rely on onError too to reset their own
    // "currently speaking" UI state when a different bubble takes over.
    if (opts.onError) utterance.onerror = opts.onError;

    window.speechSynthesis.speak(utterance);
  }

  function stop() {
    if (isSupported()) window.speechSynthesis.cancel();
  }

  function isSpeaking() {
    return isSupported() && window.speechSynthesis.speaking;
  }

  window.VoiceOutput = {
    isSupported: isSupported,
    speak: speak,
    stop: stop,
    isSpeaking: isSpeaking,
  };
})();
