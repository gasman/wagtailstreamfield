(function($) {
    window.StructBlock = function(childInitializersWithNames) {
        return function(elementPrefix) {
            for (var i = 0; i < childInitializersWithNames.length; i++) {
                var childName = childInitializersWithNames[i][0];
                var childInitializer = childInitializersWithNames[i][1];
                childInitializer(elementPrefix + '-' + childName);
            }
        };
    };
})(jQuery);
