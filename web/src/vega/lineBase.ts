export const lineBase = (width:number, height:number) => ({
  $schema: 'https://vega.github.io/schema/vega-lite/v5.json',
  width, height,
  padding: {left: 36, right: 10, top: 10, bottom: 26},
  mark: {type:'line'},
  encoding: {
    x: {field:'t', type:'quantitative', axis:{title:'t'}},
    y: {field:'y', type:'quantitative', axis:{title:'y'}}
  }
});