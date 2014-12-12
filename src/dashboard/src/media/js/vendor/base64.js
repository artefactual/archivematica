// Adapted from https://developer.mozilla.org/en-US/docs/Web/API/WindowBase64.btoa

var Base64 =
{
    // If passed string is UTF-8, decodes to bytes first before encoding.
    encode: function (str) {
        try {
            return window.btoa(str);
        } catch (InvalidCharacterError) {
            return window.btoa(unescape(encodeURIComponent(str)));
        }
    },

    // Returns a UTF-8 string if input is UTF-8, raw bytes otherwise.
    decode: function (str) {
        try {
            return decodeURIComponent(escape(window.atob(str)));
        } catch (URIError) {
            return window.atob(str);
        }
    }
};
