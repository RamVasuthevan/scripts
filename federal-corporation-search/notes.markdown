# CorpCan XML Schema

## Root Element
`<cc:corpcan>`: Namespace: `xmlns:cc="http://www.ic.gc.ca/corpcan"`
Attributes:
- `reportId`: String. "OPEN_DATA".
- `date`: xs:dateTime
Child elements:
- corporations

## Components
### corporations
Container element for corporation elements

### corporation
A specific corporation, identified by attribute "corporationId"
Child elements (all optional):
- names
- annualReturns
- acts
- statuses
- activities
- addresses
- directorLimits
- businessNumbers (optional)

### names
Container for name elements
Child elements:
- name (one or more)

### name
A corporation name
Attributes:
- code: xs:string
- effectiveDate: xs:dateTime
- expiryDate: xs:dateTime (optional)
- current: xs:boolean (optional)
Type: xs:string

### businessNumbers
Container for businessNumber elements
Child elements:
- businessNumber (exactly one)

### businessNumber
The current business number for the corporation
Type: xs:string