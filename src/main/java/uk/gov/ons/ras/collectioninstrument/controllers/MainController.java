package uk.gov.ons.ras.collectioninstrument.controllers;

import com.google.gson.Gson;
import org.apache.commons.io.IOUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.*;


import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import uk.gov.ons.ras.collectioninstrument.dao.CollectionInstrumentDao;
import uk.gov.ons.ras.collectioninstrument.dao.CollectionInstrument;

@RestController
public class MainController {

    private final Logger logger = LoggerFactory.getLogger(this.getClass());

    @Autowired
    private CollectionInstrumentDao repository;

    /**
     * Endpoint to return a basic status string.
     *
     * @return
     */
    @RequestMapping(value = "/status")
    public String available() {
        return "Collection Instrument service is running";
    }

    /**
     * Endpoint to return a requested collection instrument.
     *
     * @param reference The reference identifier for the desired instrument.
     * @return the collection instrument
     */
    @RequestMapping(value = "/collectioninstrument/{reference}", produces = "application/json", method = RequestMethod.GET)
    public ResponseEntity<CollectionInstrument> getCollectionInstrumentByReference(@PathVariable("reference") String reference) {
        logger.debug("Request for /collectioninstrument/{}", reference);
        CollectionInstrument collectionInstrument = repository.read(reference);
        if (collectionInstrument != null) {
            logger.debug(collectionInstrument.toString());
            return ResponseEntity.status(HttpStatus.OK).body(collectionInstrument);
        } else {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(null);
        }
    }

    /**
     * Endpoint to return the a collection instrument.
     *
     * @param id The database row identifier for the desired instrument.
     * @return the collection instrument
     */
    @RequestMapping(value = "/collectioninstrument/id/{id}", produces = "application/json", method = RequestMethod.GET)
    public ResponseEntity<CollectionInstrument> getCollectionInstrumentByRowId(@PathVariable("id") int id) {
        logger.debug("Request for /collectioninstrument/id/{}", id);
        CollectionInstrument collectionInstrument = repository.read(id);
        if (collectionInstrument != null) {
            logger.debug(collectionInstrument.toString());
            return ResponseEntity.status(HttpStatus.OK).body(collectionInstrument);
        } else {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(null);
        }
    }

    /**
     * Endpoint to return a list of collection instruments.
     * <p>
     * NB this endpoint can return an empty list, with 200 OK.
     *
     * @return a list of all collection instruments.
     */
    @RequestMapping(value = "/collectioninstrument", produces = "application/vnd.collection+json", method = RequestMethod.GET)
    public List<CollectionInstrument> getCollectionInstruments() {
        logger.debug("Request for /collectioninstrument");
        List<CollectionInstrument> collectionInstruments = (List<CollectionInstrument>) repository.list();
        List<CollectionInstrument> result = new ArrayList<>();
        if (collectionInstruments != null && collectionInstruments.size() > 0) {
            collectionInstruments.forEach((collectionInstrument) -> {
                result.add(collectionInstrument);
            });
        }
        return result;
    }

    @RequestMapping(value = "/collectioninstrument", method = RequestMethod.POST)
    public void collectioninstrument(@RequestBody CollectionInstrument json) {
        logger.debug("Request to create /collectioninstrument: {}", new Gson().toJson(json));
        long rowId = repository.create(json);
        logger.debug("Created new collection instrument row: " + rowId);

    }

    @RequestMapping(value = "/schema/collectioninstrument", method = RequestMethod.GET, produces = "application/json")
    public String schema() throws IOException {
        String schema = "uk.gov.ons.ras.collectioninstrument/schema.json";
        try (InputStream inputStream = MainController.class.getClassLoader().getResourceAsStream(schema)) {
            return IOUtils.toString(inputStream, "UTF8");
        }
    }

}