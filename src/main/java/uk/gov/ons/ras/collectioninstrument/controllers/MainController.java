package uk.gov.ons.ras.collectioninstrument.controllers;

import com.google.gson.Gson;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.*;


import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import uk.gov.ons.ras.collectioninstrument.dao.CollectionInstrumentDao;
import uk.gov.ons.ras.collectioninstrument.entities.CollectionInstrument;

import javax.servlet.http.HttpServletResponse;

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
     * Endpoint to return the requested collection instrument.
     *
     * @param id
     * @return the collection instrument
     */
    @RequestMapping(value = "/collectioninstrument/id/{id}", produces = "application/json", method = RequestMethod.GET)
    public ResponseEntity<CollectionInstrument> getCollectionInstrument(@PathVariable("id") Long id) {
        logger.debug("Request for /collectioninstrument/id/{}", id);
        CollectionInstrument collectionInstrument = repository.findById(id);
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
    public List<CollectionInstrument.Json> getCollectionInstruments() {
        logger.debug("Request for /collectioninstrument");
        List<CollectionInstrument> collectionInstruments = (List<CollectionInstrument>) repository.findAll();
        List<CollectionInstrument.Json> result = new ArrayList<>();
        if (collectionInstruments != null && collectionInstruments.size() > 0) {
            collectionInstruments.forEach((collectionInstrument) -> {
                result.add(collectionInstrument.getJson());
                logger.debug(collectionInstrument.getContent());
            });
        }
        return result;
    }

    @RequestMapping(value = "/collectioninstrument", method = RequestMethod.POST)
    public void collectioninstrument(@RequestBody CollectionInstrument.Json json) {
        logger.debug("Request to create /collectioninstrument: {}", new Gson().toJson(json));
        CollectionInstrument collectionInstrument = new CollectionInstrument(json);
        collectionInstrument = repository.save(collectionInstrument);
        logger.debug("Created new collection instrument: {}", collectionInstrument.getId());
    }


}