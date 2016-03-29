var statTrackChat = angular.module('statTrackChat', []);
statTrackChat.controller('ChatController', function($scope){
   var socket = io.connect('https://' + document.domain + ':'
   +location.port + '/statTrack'); 
   
   $scope.messages = [];
   $scope.searchQuery =[];
   $scope.name = '';
   $scope.text = '';
   $scope.loggedIn = '';
   
   socket.on('message', function(msg){
       console.log(msg);
       $scope.messages.push(msg);
       $scope.$apply();
       var elem = document.getElementById('msgpane');
       elem.scrollTop = elem.scrollHeight;
   });
   
   socket.on('searchDb', function(text){
        console.log(text);
        $scope.searchQuery.push(text);
        $scope.$apply();
        var elem = document.getElementById('searchTable');
       
   });
   
   socket.on('setUsername', function(username){
      console.log(username);
      console.log('test');
      $scope.loggedIn = username;
      $scope.$apply();
   });
   
   $scope.send = function send(){
       console.log('Sending message: ', $scope.text)
       socket.emit('message', $scope.text);
       $scope.text = '';
   }
   
   $scope.search = function search(){
       console.log('Searching for: ', $scope.searchText)
       socket.emit('searchDb', $scope.searchText);
       $scope.searchText = '';
   }
   
   $scope.setName = function setName(){
        socket.emit('identify', $scope.name)
   };
   
   socket.on('connect', function(){
    console.log('connected');    
   
   });
    
    
});