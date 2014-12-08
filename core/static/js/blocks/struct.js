window.StructBlock = function(childInitializersByName) {
    return function(childParams, prefix) {
        for (var childName in childParams) {
            var childInitializer = childInitializersByName[childName];
            var childParam = childParams[childName];
            var childPrefix = prefix + '-' + childName;
            childInitializer(childParam, childPrefix);
        }
    };
};
