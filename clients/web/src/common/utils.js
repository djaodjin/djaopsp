// Per: https://slavik.meltser.info/the-efficient-way-to-create-guid-uuid-in-javascript-with-explanation/
export const getUniqueId = () => {
  function _p8(s) {
    var p = (Math.random().toString(16) + '000000000').substr(2, 8)
    return s ? '-' + p.substr(0, 4) + '-' + p.substr(4, 4) : p
  }
  return _p8() + _p8(true) + _p8(true)
}

// Per: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/random
export function getRandomInt(min, max) {
  min = Math.ceil(min)
  max = Math.floor(max)
  return Math.floor(Math.random() * (max - min)) + min //The maximum is exclusive and the minimum is inclusive
}

export function template(strings, ...keys) {
  return function (params) {
    const dict = params || {}
    const result = [strings[0]]
    keys.forEach(function (key, i) {
      result.push(dict[key], strings[i + 1])
    })
    return result.join('')
  }
}
