const functions = require('firebase-functions');
const url = require('url');
const {
    dialogflow,
    Image,
    Permission,
    NewSurface,
    Suggestions,
} = require('actions-on-google');
const {ssml} = require('./util');

/**
 * Depending on user verification status, save data either to dialog session
 * (conv.data) or cross-session storage (conv.user.storage). Users must be
 * verified to use cross-session storage, but it provides ideal UX.
 * https://developers.google.com/actions/assistant/guest-users
 * @param {object} conv - The conversation instance.
 * @return {Object}
 */
const userData = (conv) => {
    return conv.user.verification === 'VERIFIED' ? conv.user.storage : conv.data;
};

const app = dialogflow({
    debug: true
});

// const checkCapabilities = (capList, capability) => {
//     capList.forEach((cap) => {
//         if (cap.name.valueOf() === capability.valueOf()){
//             return true;
//         }
//     });
//     return false;
// };

const config = functions.config();
const STATIC_MAPS_ADDRESS = 'https://maps.googleapis.com/maps/api/staticmap';
const STATIC_MAPS_SIZE = '640x640';

const stops = [
    {
        name: "Hereford",
        latitude: 38.029565, 
        longitude: -78.519102
    },
    {
        name: "Hereford Top",
        latitude: 38.030525, 
        longitude: -78.519568
    }
];


const locationResponse = (location, points, speech) => {
    const staticMapsURL = url.parse(STATIC_MAPS_ADDRESS, true);
    staticMapsURL.query = {
        key: config.maps.key,
        size: STATIC_MAPS_SIZE,
    };
    let markers = '';
    points.forEach((point, index) => {
        markers += point.latitude.toString() + ',' + point.longitude.toString();
        if ((index + 1) < points.length) {
            markers += '|';
        }
    });
    // staticMapsURL.query.center = city;
    staticMapsURL.query.markers = markers;
    const mapViewURL = url.format(staticMapsURL);
    console.log("MAPVIEWURL: " + mapViewURL);
    return [
        speech,
        new Image({
            url: mapViewURL,
            alt: 'Map',
        }),
    ];
};

/**
 * Shows the location of the user with a preference for a screen device.
 * If on a speaker device, asks to transfer dialog to a screen device.
 * Reads location from userStorage.
 * @param {object} conv - The conversation instance.
 * @return {Void}
 */
const showLocationOnScreen = (conv) => {
    const capability = 'actions.capability.SCREEN_OUTPUT';
    return conv.close(...responses.sayLocation(conv.device.location, stops));
    // if (conv.surface.capabilities.has(capability) || !conv.available.surfaces.capabilities.has(capability)) {
    //     // return conv.close(...responses.sayLocation(userData(conv).location));
    //     return conv.close(...responses.sayLocation(conv.device.location));
    // }
    // conv.ask(new NewSurface({
    //     context: responses.newSurfaceContext,
    //     notification: responses.notificationText,
    //     capabilities: capability,
    // }));
};

const responses = {
    sayName: (name) => ssml`
        <speak>
        I am reading your mind now.
        <break time="2s"/>
        This is easy, you are ${name}
        <break time="500ms"/>
        I hope I pronounced that right.
        <break time="500ms"/>
        Okay! I am off to read more minds.
        </speak>
    `,
    sayLocation: (location, points) => locationResponse(location, points, ssml`
        <speak>
        These are the stops nearest to your location.
        </speak>
    `),
    greetUser: ssml`
        <speak>
        Welcome to Bus Buddy!
        <break time="500ms"/>
        Have a bus to catch?
        </speak>
    `,
    unhandledDeepLinks: (input) => ssml`
        <speak>
        Welcome to your Psychic! I can guess many things about you,
        but I cannot make guesses about ${input}.
        Instead, I shall guess your name or location. Which do you prefer?
        </speak>
    `,
    error: ssml`
        <speak>
        An error as occurred.
        Please try again later.
        </speak>
    `,
    suggestUses: ssml`
        <speak>
        Ask me about buses or stops near you!
        </speak>
    `,
    permissionReason: 'To find buses near you',
    requestedPermissions: ['DEVICE_PRECISE_LOCATION'],
    newSurfaceContext: 'To show you your location',
    notificationText: 'See you where you are...',
};

app.intent('Default Welcome Intent', (conv) => {
    // userData(conv) = {}
    // Uncomment above to delete the cached permissions on each request
    // to force the app to request new permissions from the user
    // conv.ask(responses.greetUser);
    // Location permissions only work for verified users
    if (conv.user.verification === 'VERIFIED') {
        // Logged In

    } else {
        // TODO: Log User In
        
    }
    const { permissions } = conv.user;
    if (!permissions.includes('DEVICE_PRECISE_LOCATION')) {
        conv.ask(new Permission({
            context: responses.permissionReason,
            permissions: responses.requestedPermissions,
        }));
    }
    conv.ask(responses.suggestUses);
    conv.ask(new Suggestions([
        'When is next Northline',
        'Stops near me'
    ]));
});

// app.intent('Permission', (conv) => {
//     const permissions = ['NAME'];
//     let context = 'To address you by name';
//     // Location permissions only work for verified users
//     // https://developers.google.com/actions/assistant/guest-users
//     if (conv.user.verification === 'VERIFIED') {
//         // Could use DEVICE_COARSE_LOCATION instead for city, zip code
//         permissions.push('DEVICE_PRECISE_LOCATION');
//         context += ' and know your location';
//     }
//     const options = {
//         context,
//         permissions,
//     };
//     conv.ask(new Permission(options));
// });

app.intent('Get Location', (conv, params, confirmationGranted) => {
    // Also, can access latitude and longitude
    const { location } = conv.device;
    // const { latitude, longitude } = location.coordinates;
    // const {name} = conv.user;
    if (confirmationGranted && location) {
        // conv.ask(`Okay, I see you're at ` +
        // `${location.formattedAddress}` + `${latitude}, ${longitude}`);f
        conv.ask('What would you like to do?');
        conv.ask(new Suggestions([
            'When is next Northline',
            'Show stops near me'
        ]));
    } else {
        throw new Error('Permission not granted');
    }
    // conv.ask(`Would you like to try another helper?`);
    // conv.ask(new Suggestions([
    //     'Confirmation',
    //     'DateTime',
    //     'Place',
    // ]));
});

app.intent('Get Next Bus', (conv, params) => {
    const {location} = conv.device;
    // Location permissions only work for verified users
    // https://developers.google.com/actions/assistant/guest-users
    if (conv.user.verification === 'VERIFIED') {
        // Could use DEVICE_COARSE_LOCATION instead for city, zip code
        if (location){
            const { request_type: requestType, bus_line: busLine } = params;
            // conv.close(`You requested ${requestType} for the bus line ${ busLine }`);
            showLocationOnScreen(conv);
        } else {
            // request location
        }
    } else {
        // TODO: sign in user
        conv.close(`You must be signed in so Bus Buddy can access your location.`);
    }
    // const options = {
    //     context,
    //     permissions,
    // };
    // conv.ask(new Permission(options));
});

app.catch((conv, e) => {
    console.error(e);
    conv.close(responses.error);
});

// Exported function name must be 'dialogflowFirebaseFulfillment'
exports.dialogflowFirebaseFulfillment = functions.https.onRequest(app);