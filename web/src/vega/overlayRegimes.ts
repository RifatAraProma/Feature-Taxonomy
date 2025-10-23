export const overlayChangePoints = (dataName='changePoints') => ([{
  data: {name: dataName},
  mark: {type:'rule'},
  encoding: {
    x: {field:'t', type:'quantitative'},
    color: {value:'#888'}, opacity: {value:0.7},
    tooltip: [{field:'t'},{field:'fromBaseline'},{field:'toBaseline'}]
  }
}]);