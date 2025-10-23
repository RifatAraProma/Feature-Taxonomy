export const overlayExtrema = (dataName='extrema') => ([{
  data: {name: dataName},
  mark: {type:'point', filled:true, size:60},
  encoding: {
    x: {field:'t', type:'quantitative'},
    y: {field:'y', type:'quantitative'},
    color: {field:'type', type:'nominal', scale:{domain:['max','min'], range:['#d7191c','#2c7bb6']}, legend:null},
    tooltip: [{field:'type'},{field:'t'},{field:'y'}]
  }
}]);