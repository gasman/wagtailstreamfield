(function($) {
    window.Chooser = function(definitionPrefix) {
        return function(/* no parameters needed here; all chooser instances have the same JS constructor */) {
            return function(elementPrefix) {
                $('#' + elementPrefix + '-button').click(function() {
                    alert('hello, I am a chooser for ' + elementPrefix + ', which is of type ' + definitionPrefix);
                });
            };
        };
    };
})(jQuery);
