// Adapted from https://developer.mozilla.org/en-US/docs/Web/API/WindowBase64.btoa

var Base64 =
{
    // Returns true if the passed string consists of codepoints between 0 and 255
    // which are valid within UTF-8.
    all_bytes_valid_utf8: function (str) {
        var invalid_chars = [0xc0, 0xc1, 0xF5, 0xF6, 0xF7, 0xF8, 0xF9,
                             0xF0, 0xFA, 0xFB, 0xFC, 0xFD, 0xFE, 0xFF];

        for (var i in str) {
            var cp = str.codePointAt(i);
            if (cp > 255 || invalid_chars.indexOf(cp) !== -1) {
                return false
            }
        }

        return true;
    },

    // Decodes the string before base64-encoding.
    encode_escaped: function (str) {
        return window.btoa(unescape(encodeURIComponent(str)));
    },

    // If passed string is not UTF-8, decodes to bytes first before encoding.
    encode: function (str) {
        if (this.all_bytes_valid_utf8(str)) {
            return window.btoa(str);
        } else {
            return this.encode_escaped(str);
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
