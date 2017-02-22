package uk.gov.ons.ras.collectioninstrument.dao;

import com.google.gson.Gson;
import org.postgresql.util.PGobject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.PreparedStatementCreator;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.sql.*;
import java.util.List;
import java.util.Map;

/**
 * Class for accessing the Collection Instrument table.
 * <p>
 * We're using JDBC so that we can get access to the Json column type in Postgres,
 * which seems to be tricky and more complex to do through Hibernate.
 * <p>
 * Credit to: http://sivalabs.in/2016/03/springboot-working-with-jdbctemplate/
 * and to: http://www.pateldenish.com/2013/05/inserting-json-data-into-postgres-using-jdbc-driver.html
 * and for jsonb query parameter syntak: http://stackoverflow.com/questions/37422886/jdbc-prepared-statement-parameter-inside-json
 */
@Repository
public class CollectionInstrumentDao {

    private final Logger logger = LoggerFactory.getLogger(this.getClass());

    /**
     * NB JdbcTemplate is thread-safe: http://stackoverflow.com/questions/467324/spring-jdbctemplate-and-threading
     */
    @Autowired
    private JdbcTemplate jdbcTemplate;

    static final String selectAll = "select * from ras_collection_instruments";
    static final String selectReference = "select * from ras_collection_instruments " +
            "where content @> ?::jsonb";
    static final String selectId = "select * from ras_collection_instruments where id=?";
    static final String insert = "insert into ras_collection_instruments (content) values (?)";

    /**
     * Creates a new Collection Instrument record.
     *
     * @param collectionInstrument The {@link CollectionInstrument} instance to be stored.
     */
    public long create(CollectionInstrument collectionInstrument) {
        KeyHolder holder = new GeneratedKeyHolder();
        jdbcTemplate.update(new PreparedStatementCreator() {
            @Override
            public PreparedStatement createPreparedStatement(Connection connection) throws SQLException {
                PreparedStatement ps = connection.prepareStatement(insert, Statement.RETURN_GENERATED_KEYS);
                ps.setObject(1, toJsonb(collectionInstrument));
                return ps;
            }
        }, holder);

        // Postgres returns a List of maps for this insert operation:
        List<Map<String, Object>> keys = holder.getKeyList();
        return ((Long)keys.get(0).get("id")).longValue();
    }

    /**
     * Reads collection instrument details for the given reference.
     *
     * @param reference The human-readable reference for the collection instrument.
     * @return A {@link CollectionInstrument} instance representing the database row.
     */
    @Transactional(readOnly = true)
    public CollectionInstrument read(String reference) {
        CollectionInstrument result = null;
        try {
            result = jdbcTemplate.queryForObject(
                    selectReference,
                    new Object[]{"{\"reference\":\""+reference+"\"}"}, new CollectionInstrumentMapper());
        } catch (EmptyResultDataAccessException e) {
            logger.debug("No result found for reference " + reference);
        }
        return result;
    }

    /**
     * Reads collection instrument details for the given database row ID.
     *
     * @param id The database row ID.
     * @return A {@link CollectionInstrument} instance representing the database row.
     */
    @Transactional(readOnly = true)
    public CollectionInstrument read(int id) {
        CollectionInstrument result = null;
        try {
            result = jdbcTemplate.queryForObject(
                    selectId,
                    new Object[]{id}, new CollectionInstrumentMapper());
        } catch (EmptyResultDataAccessException e) {
            logger.debug("No result found for row ID " + id);
        }
        return result;
    }

    /**
     * @return a list of the collection instruments from the database.
     */
    @Transactional(readOnly = true)
    public List<CollectionInstrument> list() {
        return jdbcTemplate.query(selectAll,
                new CollectionInstrumentMapper());
    }

    /**
     * Converts a {@link CollectionInstrument} instance to a {@link PGobject} compatible with the json column type.
     *
     * @param collectionInstrument The instance to be converted.
     * @return A {@link PGobject}
     * @throws SQLException If an error occurs.
     */
    private PGobject toJsonb(CollectionInstrument collectionInstrument) throws SQLException {
        PGobject jsonb = new PGobject();
        jsonb.setType("json");
        jsonb.setValue(new Gson().toJson(collectionInstrument));
        return jsonb;
    }

    /**
     * RowMapper implementation to load collection instrument data.
     */
    static class CollectionInstrumentMapper implements RowMapper<CollectionInstrument> {
        public CollectionInstrument mapRow(ResultSet rs, int rowNum) throws SQLException {
            CollectionInstrument content = new Gson().fromJson(rs.getString("content"), CollectionInstrument.class);
            //content.id = rs.getInt("id");
            return content;
        }
    }
}



