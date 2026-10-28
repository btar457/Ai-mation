import fs from 'fs';
import {feature, mesh} from 'topojson-client';
const topo = JSON.parse(fs.readFileSync('node_modules/world-atlas/countries-50m.json'));
const o = topo.objects.countries;
const fc = feature(topo, o);
const want = ['Iraq','Syria','Turkey','Iran','Saudi Arabia','Kuwait','Jordan','Israel','Lebanon','Palestine','Egypt','Qatar','Bahrain','United Arab Emirates','Armenia','Azerbaijan','Georgia','Cyprus','Oman','Yemen','Turkmenistan','Sudan'];
const countries = fc.features.filter(f=>want.includes(f.properties.name));
const n = g => g.properties.name;
const pair = (A,B) => mesh(topo, o, (a,b)=> (n(a)===A&&n(b)===B)||(n(a)===B&&n(b)===A));
const meshes = {
  syria: pair('Iraq','Syria'), jordan: pair('Iraq','Jordan'), saudi: pair('Iraq','Saudi Arabia'),
  kuwait: pair('Iraq','Kuwait'), iran: pair('Iraq','Iran'), turkey: pair('Iraq','Turkey'),
  kuwaitSaudi: pair('Kuwait','Saudi Arabia'),
};
for (const [k,v] of Object.entries(meshes)) console.log(k, v.coordinates.length, JSON.stringify(v.coordinates[0][0]), JSON.stringify(v.coordinates[0].at(-1)));
fs.writeFileSync('src/geo.json', JSON.stringify({countries:{type:'FeatureCollection',features:countries}, meshes}));
