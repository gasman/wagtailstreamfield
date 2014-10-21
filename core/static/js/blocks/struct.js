(function($) {
    window.StructBlock = function(childConstructorsWithNames) {
        return {
            'init': function(elementPrefix) {
                for (var i = 0; i < childConstructorsWithNames.length; i++) {
                    var childName = childConstructorsWithNames[i][0];
                    var childConstructor = childConstructorsWithNames[i][1];
                    childConstructor.init(elementPrefix + '-' + childName);
                }
            }
        };
    };
})(jQuery);
