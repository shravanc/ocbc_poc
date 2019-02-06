var app=angular.module('docketly-app', []);
//var UI_URL = "http:///54.245.29.69:8090/extract";
var UI_URL = "http:///localhost:8090/extract";

app.controller('DocketlyHomeController', ['$scope','$http',function($scope, $http){
    $scope.extractData=function(){
        $scope.isUploading = true;
        var formData = new FormData(document.querySelector('#upload-form'));
        var uploadUrl = UI_URL;
        $http.post(uploadUrl, formData,{
            transformRequest: angular.identity,
            headers: {'Content-Type': undefined}
        }).then(
            function successCallback(response) {
                $scope.isUploading = false;
                $scope.court_info = {'hello': 'cool'}; //response.data.data;
                var pdf_url = /Users/shravanc/learning_pyt/open_cv_learning/pdfs/ocbc_1.DPI_73.pdf 
                PDFObject.embed(pdf_url, "#pdf-container");
            }, 
            function errorCallback(response) {
                $scope.isUploading = false;
                console.log('response');
            });
    };
}]);


