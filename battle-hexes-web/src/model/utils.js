export class Utils {
  static cloneValue(value) {
    if (Array.isArray(value)) {
      return value.map((item) => Utils.cloneValue(item));
    }

    if (value && typeof value === 'object') {
      const clone = {};
      for (const [key, nestedValue] of Object.entries(value)) {
        clone[key] = Utils.cloneValue(nestedValue);
      }
      return clone;
    }

    return value;
  }
}
