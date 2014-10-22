(function($) {
    window.StreamBlock = function(childDefs) {
        var childConstructorsByName = {};
        for (var i = 0; i < childDefs.length; i++) {
            childConstructorsByName[childDefs[i].name] = childDefs[i].initializer;
        }
        return {
            'init': function(elementPrefix) {
                var countField = $('#' + elementPrefix + '-count');
                var list = $('#' + elementPrefix + '-list');

                /* initialise children */
                var count = parseInt(countField.val(), 10);
                for (var i = 0; i < count; i++) {
                    var blockType = $('#' + elementPrefix + '-' + i + '-type').val();
                    var childConstructor = childConstructorsByName[blockType];
                    if (childConstructor) {
                        childConstructor.init(elementPrefix + '-' + i + '-item');
                    }
                }
            }
        };
    };
})(jQuery);
