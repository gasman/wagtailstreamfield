(function($) {
    window.Chooser = function(definitionPrefix) {
        return {
            'init': function(elementPrefix) {
                $('#' + elementPrefix + '-button').click(function() {
                    alert('hello, I am a chooser for ' + elementPrefix + ', which is of type ' + definitionPrefix);
                });
            }
        };
    };
})(jQuery);
