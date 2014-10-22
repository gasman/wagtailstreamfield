(function($) {
    window.StreamBlock = function(childDefs) {
        var childInitializersByName = {};
        for (var i = 0; i < childDefs.length; i++) {
            childInitializersByName[childDefs[i].name] = childDefs[i].initializer;
        }
        return function(elementPrefix) {
            var countField = $('#' + elementPrefix + '-count');
            var list = $('#' + elementPrefix + '-list');

            /* initialise children */
            var count = parseInt(countField.val(), 10);
            for (var i = 0; i < count; i++) {
                var blockType = $('#' + elementPrefix + '-' + i + '-type').val();
                var childInitializer = childInitializersByName[blockType];
                if (childInitializer) {
                    childInitializer(elementPrefix + '-' + i + '-item');
                }
            }
        };
    };
})(jQuery);
