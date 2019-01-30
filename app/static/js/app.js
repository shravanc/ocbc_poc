var app=angular.module('rbc-app', []);
//var UI_URL = "http://54.190.155.131:8090/extract"
var UI_URL = "http://localhost:6789/extract"

app.controller('RBCHomeController', ['$scope','$http',function($scope, $http){
    this.$onInit = function () {
        $("#result_table").show();
    };

    $scope.extractData=function(){
        $("#upload_panel_view").LoadingOverlay("show", {
        background  : "rgba(231, 250, 252, 0.5)"
        });
        var formData = new FormData(document.querySelector('#upload-form'));
        var uploadUrl=UI_URL;
        $http.post(uploadUrl, formData,{
            transformRequest: angular.identity,
            headers: {'Content-Type': undefined}
        })
        .then(
            function successCallback(response) {
                $("#upload_panel_view").LoadingOverlay("hide", {
                    background  : "rgba(231, 250, 252, 0.5)"
                });
                $scope.pages=response.data.data;
              }, 
            function errorCallback(response) {
                $("#upload_panel_view").LoadingOverlay("hide", {
                    background  : "rgba(231, 250, 252, 0.5)"
                });
                console.log('response');
              });
    };

}]);


