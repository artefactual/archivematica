function setupAIPBrowser(directory) {

  var explorer = new FileExplorer({
    el: $('#explorer'),
    levelTemplate: $('#template-dir-level').html(),
    entryTemplate: $('#template-dir-entry').html()
  });

  explorer.options.actionHandlers = [];

  explorer.refresh(directory);
}
