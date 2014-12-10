(function($) {
    window.Chooser = function(definitionPrefix) {
        return function(valueDef, elementPrefix) {
            /* valueDef will always be null and is ignored here; JS behaviour is the same regardless of the
            block's value, so nothing meaningful is passed for js_initializer_param */
            $('#' + elementPrefix + '-button').click(function() {
                alert('hello, I am a chooser for ' + elementPrefix + ', which is of type ' + definitionPrefix);
            });
        };
    };
})(jQuery);
