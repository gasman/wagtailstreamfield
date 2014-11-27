window.StructBlock = function(childMetaInitializersByName) {
    return function(childParams) {
        var childInitialisers = {};
        for (var childName in childParams) {
            var childParam = childParams[childName];
            var childMetaInitializer = childMetaInitializersByName[childName];
            childInitialisers[childName] = childMetaInitializer.apply(null, childParam);
        }

        return function(prefix) {
            for (var childName in childInitialisers) {
                childInitialisers[childName](prefix + '-' + childName);
            }
        };
    }
};
